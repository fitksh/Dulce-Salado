import json
from datetime import time
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from .cart import calculate_cart, product_revision
from .models import BusinessSettings, Category, OpeningInterval, Product
from .whatsapp import message_configuration, whatsapp_message, whatsapp_preview
from .whatsapp_templates import (
    DEFAULT_MESSAGE_TEMPLATE,
    DEFAULT_PRODUCT_TEMPLATE,
    validate_message_template,
    validate_product_template,
)


@override_settings(WHATSAPP_PHONE="5491100000000")
class MessageTemplateTests(TestCase):
    def setUp(self):
        self.business = BusinessSettings.objects.create(address="Dirección de prueba", hours_initialized=True)
        category = Category.objects.create(name="QA", slug="qa")
        self.product = Product.objects.create(category=category, name="Gelatina {total}", brand="Marca QA", description="Paquete 500 gr",
                                              sale_unit="paquete", retail_price=Decimal("1900"), wholesale_price=Decimal("1700"))
        self.product.refresh_from_db()
        self.item = {"id": self.product.pk, "quantity": "2", "price_type": "retail", "sale_unit": "paquete", "revision": product_revision(self.product)}

    def post(self, route, revision=None):
        return self.client.post(reverse(route), {"items": json.dumps([self.item]), "accepted": "yes",
                                "message_revision": message_configuration()["revision"] if revision is None else revision})

    def test_missing_configuration_uses_defaults_without_creating_rows(self):
        self.business.delete()
        config = message_configuration()
        self.assertEqual(config["message"], DEFAULT_MESSAGE_TEMPLATE)
        self.assertEqual(config["product"], DEFAULT_PRODUCT_TEMPLATE)
        self.assertFalse(BusinessSettings.objects.exists())

    def test_custom_text_emojis_order_and_literal_product_braces(self):
        self.business.whatsapp_message_template = "Hola 👋\n{productos}\n💰 {total}\nGracias ❤️"
        self.business.whatsapp_product_template = "🛍️ {producto}\n{cantidad} {unidad} × {precio} = {subtotal}\n{marca}\n{descripcion}"
        self.business.full_clean()
        self.business.save()
        message = whatsapp_message(calculate_cart([self.item]))
        self.assertEqual(message, "Hola 👋\n🛍️ Gelatina {total}\n2 paquete × $ 1.900 = $ 3.800\nMarca QA\nPaquete 500 gr\n💰 $ 3.800\nGracias ❤️")
        self.product.refresh_from_db()
        self.assertEqual(self.product.wholesale_price, Decimal("1700"))

    def test_optional_lines_disappear_only_when_their_values_are_blank(self):
        self.product.brand = "  "
        self.product.description = ""
        self.product.save()
        message = whatsapp_message(calculate_cart([self.item]))
        self.assertNotIn("• Marca:", message)
        self.assertNotIn("• Presentación:", message)
        self.assertIn("Precio: $ 1.900 por paquete", message)
        self.assertIn("Cantidad: 2 paquetes", message)

    def test_optional_brand_on_a_required_line_never_hides_product_or_money(self):
        self.product.brand = ""
        self.product.save()
        self.business.whatsapp_product_template = "{producto} / {marca}\n{cantidad} {unidad} × {precio} = {subtotal}"
        self.business.full_clean()
        self.business.save()
        message = whatsapp_message(calculate_cart([self.item]))
        self.assertIn("Gelatina {total}", message)
        self.assertIn("2 paquete × $ 1.900 = $ 3.800", message)

    def test_unknown_fields_access_formats_conversions_and_missing_data_are_rejected(self):
        for template in ("{productos}", "{productos} {total} {secreto}", "{productos} {total.__class__}",
                         "{productos} {total!r}", "{productos} {total:1000000}", "{productos} {total", "{productos} {total}\x00"):
            with self.subTest(template=template), self.assertRaises(ValidationError):
                validate_message_template(template)
        for template in ("{producto}", DEFAULT_PRODUCT_TEMPLATE + "{producto.name}"):
            with self.assertRaises(ValidationError):
                validate_product_template(template)
        validate_message_template("{{Texto literal}} {productos} {total}")

    def test_invalid_database_template_falls_back_without_executing_or_losing_cart(self):
        BusinessSettings.objects.filter(pk=1).update(whatsapp_message_template="{request.user.password}")
        response = self.post("cart_review")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["message"].startswith("Hola!"))
        self.assertIn("Gelatina {total}", response.context["message"])
        self.assertIn("$ 3.800", response.context["message"])

    def test_template_change_during_review_requires_new_acceptance(self):
        preview = self.post("cart_review")
        previous = preview.context["message_revision"]
        self.business.whatsapp_message_template = "Hola nuevo 👋\n{productos}\nTotal: {total}"
        self.business.save()
        changed = self.post("cart_whatsapp", previous)
        self.assertNotContains(changed, 'id="whatsapp-ready"')
        self.assertContains(changed, "El mensaje del comercio cambió")
        self.assertIn("Hola nuevo 👋", changed.context["message"])
        ready = self.post("cart_whatsapp", changed.context["message_revision"])
        self.assertContains(ready, 'id="whatsapp-ready"')
        self.assertEqual(parse_qs(urlparse(ready.context["ready_url"]).query)["text"], [changed.context["message"]])

    def test_missing_message_revision_requires_review(self):
        response = self.post("cart_whatsapp", "")
        self.assertNotContains(response, 'id="whatsapp-ready"')
        self.assertContains(response, "Revisá el texto actualizado")

    def test_admin_save_preview_validation_permissions_and_escape(self):
        owner = get_user_model().objects.create_superuser("message-owner", "", "qa-only")
        self.client.force_login(owner)
        url = reverse("admin:catalog_businesssettings_change", args=[1])
        data = {"address": self.business.address, "hours_initialized": "on", "maps_url": "",
                "whatsapp_message_template": "Hola 🛍️ <script>ejemplo</script>\n{productos}\n{total}",
                "whatsapp_product_template": DEFAULT_PRODUCT_TEMPLATE,
                "opening_intervals-TOTAL_FORMS": "0", "opening_intervals-INITIAL_FORMS": "0"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.business.refresh_from_db()
        self.assertEqual(self.business.address, "Dirección de prueba")
        self.assertTrue(self.business.hours_initialized)
        self.assertEqual(self.business.whatsapp_message_template, data["whatsapp_message_template"])
        response = self.client.get(url)
        self.assertContains(response, "Vista previa con datos de ejemplo")
        self.assertContains(response, "&lt;script&gt;ejemplo&lt;/script&gt;")
        self.assertNotContains(response, "<script>ejemplo</script>")
        self.assertIn("Gelatina sin sabor (ejemplo)", whatsapp_preview(self.business))
        self.assertIn("$ 9.100", whatsapp_preview(self.business))
        data["whatsapp_message_template"] = "Sin los campos necesarios"
        self.assertContains(self.client.post(url, data), "Conservá estos campos")
        self.business.refresh_from_db()
        self.assertNotEqual(self.business.whatsapp_message_template, data["whatsapp_message_template"])
        self.client.force_login(get_user_model().objects.create_user("message-staff", is_staff=True))
        self.assertEqual(self.client.post(url, data).status_code, 403)


class MessageTemplateMigrationTests(TransactionTestCase):
    def test_additive_migration_preserves_existing_products_business_users_and_hours(self):
        old = [("catalog", "0005_product_presentations")]
        current = [("catalog", "0007_whatsapp_subtotal_label")]
        executor = MigrationExecutor(connection)
        executor.migrate(old)
        try:
            apps = executor.loader.project_state(old).apps
            business = apps.get_model("catalog", "BusinessSettings").objects.create(
                address="Dirección existente", maps_url="https://maps.app.goo.gl/qa", hours_initialized=True)
            apps.get_model("catalog", "OpeningInterval").objects.create(business=business, weekday=0, opens_at=time(9), closes_at=time(12))
            category = apps.get_model("catalog", "Category").objects.create(name="Existente", slug="existente")
            apps.get_model("catalog", "Product").objects.create(category=category, name="Original", retail_price="123.45", wholesale_price="99.10", description="Original", image="products/original.webp")
            owner = get_user_model().objects.create_superuser("migration-owner", "", "qa-only")
            fields = [field.name for field in apps.get_model("catalog", "BusinessSettings")._meta.fields]
            before_business = apps.get_model("catalog", "BusinessSettings").objects.values(*fields).get()
            before_products = list(apps.get_model("catalog", "Product").objects.values())
            before_hours = list(apps.get_model("catalog", "OpeningInterval").objects.values())
            MigrationExecutor(connection).migrate(current)
            self.assertEqual(BusinessSettings.objects.values(*fields).get(), before_business)
            self.assertEqual(list(Product.objects.values()), before_products)
            self.assertEqual(list(OpeningInterval.objects.values()), before_hours)
            self.assertTrue(get_user_model().objects.get(pk=owner.pk).is_superuser)
            self.assertEqual(BusinessSettings.objects.get().whatsapp_message_template, MigrationExecutor(connection).loader.project_state(current).apps.get_model("catalog", "BusinessSettings")._meta.get_field("whatsapp_message_template").default)
            self.assertEqual(BusinessSettings.objects.get().whatsapp_product_template, MigrationExecutor(connection).loader.project_state(current).apps.get_model("catalog", "BusinessSettings")._meta.get_field("whatsapp_product_template").default)
        finally:
            MigrationExecutor(connection).migrate([("catalog", "0009_whatsapp_readable_format")])
