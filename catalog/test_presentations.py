import json
import tempfile
from decimal import Decimal
from io import BytesIO
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from PIL import Image

from .admin import ProductAdminForm
from .cart import calculate_cart, product_revision
from .csv_import import create_from_preview, preview_rows
from .models import Category, Product
from .whatsapp import whatsapp_message


class PresentationTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="QA", slug="qa")

    def test_six_units_fixed_step_and_database_rejects_other_steps(self):
        self.assertEqual(Product.SaleUnit.values, ["100 gr", "kg", "caja", "pack", "paquete", "bolsa"])
        for unit in Product.SaleUnit.values:
            product = Product(category=self.category, name="Chips", sale_unit=unit, retail_price="10")
            product.full_clean()
            product.save()
            cart = calculate_cart([{"id": product.pk, "quantity": "3", "price_type": "retail"}])
            self.assertEqual(cart["total"], Decimal("30"))
            self.assertFalse(calculate_cart([{"id": product.pk, "quantity": "0.3", "price_type": "retail"}])["valid"])
            for step in (Decimal("0.1"), Decimal("2")):
                product.quantity_step = step
                with self.assertRaises(ValidationError):
                    product.full_clean()
                with self.assertRaises(IntegrityError), transaction.atomic():
                    product.save()

    def test_csv_keeps_different_presentations_and_omits_only_same_presentation(self):
        rows = [{"number": index + 2, "values": ["QA", "Chips", "Marca", description, unit, "1", "100", "90", "", "Sí"]}
                for index, (unit, description) in enumerate([("100 gr", "Suelto"), ("kg", "Suelto"),
                                                            ("paquete", "500 gr"), ("paquete", "1 kg")])]
        preview = preview_rows(rows)
        self.assertEqual((preview.new_count, preview.error_count), (4, 0))
        self.assertEqual(create_from_preview(rows, preview.fingerprint), (4, 0))
        again = preview_rows(rows)
        self.assertEqual((again.new_count, again.duplicate_count), (0, 4))

    def test_fractional_legacy_cart_blocks_both_review_and_whatsapp_without_rounding(self):
        product = Product.objects.create(category=self.category, name="Chips", retail_price="100")
        item = {"id": product.pk, "quantity": "0.3", "price_type": "retail", "sale_unit": "kg", "revision": product_revision(product)}
        for route in ("cart_refresh", "cart_review", "cart_whatsapp"):
            response = self.client.post(reverse(route), {"items": json.dumps([item]), "accepted": "yes"})
            self.assertEqual(response.context["cart"]["items"][0]["quantity"], "0.3")
            self.assertFalse(response.context["cart"]["valid"])
            self.assertNotContains(response, 'id="whatsapp-ready"')

    def test_cart_and_whatsapp_identify_presentations_with_same_name_and_unit(self):
        items = []
        for description in ("500 gr", "1 kg"):
            product = Product.objects.create(category=self.category, name="Chips", description=description,
                                             sale_unit="paquete", retail_price="100")
            items.append({"id": product.pk, "quantity": "2", "price_type": "retail"})
        cart = calculate_cart(items)
        self.assertEqual(cart["total"], Decimal("400"))
        response = self.client.post(reverse("cart_refresh"), {"items": json.dumps(items)})
        for description in ("500 gr", "1 kg"):
            self.assertContains(response, description)
            self.assertIn("Cantidad: 2 paquetes de " + description.replace("gr", "g"), whatsapp_message(cart))

    def test_description_change_requires_whatsapp_review(self):
        product = Product.objects.create(category=self.category, name="Chips", description="500 gr", retail_price="100")
        item = {"id": product.pk, "quantity": "1", "price_type": "retail", "revision": product_revision(product)}
        Product.objects.filter(pk=product.pk).update(description="1 kg")
        response = self.client.post(reverse("cart_whatsapp"), {"items": json.dumps([item]), "accepted": "yes"})
        self.assertTrue(response.context["cart"]["notices"])
        self.assertNotContains(response, 'id="whatsapp-ready"')


class RepeatedAdminTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create_superuser("presentation-admin", "", "qa-only"))
        self.category = Category.objects.create(name="QA", slug="qa")
        self.url = reverse("admin:catalog_product_add")
        self.data = {"category": self.category.pk, "name": "Chips", "brand": "QA", "description": "500 gr",
                     "sale_unit": "paquete", "retail_price": "100", "wholesale_price": "90",
                     "wholesale_condition": "Consultar", "is_active": "on", "_addanother": "1"}

    def test_repeat_prefills_data_and_creates_independent_presentation_with_changed_fields(self):
        response = self.client.post(self.url, self.data)
        location = response["Location"]
        self.assertIn("copy", parse_qs(urlparse(location).query))
        form = self.client.get(location).context["adminform"].form
        for field in ("name", "brand", "description", "sale_unit", "wholesale_condition"):
            self.assertEqual(form[field].value(), self.data[field])
        self.assertNotIn("quantity_step", form.fields)
        self.assertNotContains(self.client.get(location), 'name="_continue"')
        invalid = {**self.data, "retail_price": "-1"}
        self.assertEqual(self.client.post(location, invalid).status_code, 200)
        self.assertEqual(Product.objects.count(), 1)
        response = self.client.post(location, {**self.data, "sale_unit": "kg", "description": "A granel", "retail_price": "200"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(list(Product.objects.order_by("pk").values_list("sale_unit", "retail_price")),
                         [("paquete", Decimal("100")), ("kg", Decimal("200"))])

    def test_repeated_image_has_own_file_and_can_be_replaced_without_losing_original(self):
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            content = BytesIO()
            Image.new("RGB", (40, 60), "orange").save(content, "PNG")
            response = self.client.post(self.url, {**self.data, "image": SimpleUploadedFile("qa.png", content.getvalue())})
            source = Product.objects.get()
            response = self.client.post(response["Location"], {**self.data, "description": "Otra presentación"})
            self.assertEqual(response.status_code, 302)
            clone = Product.objects.exclude(pk=source.pk).get()
            self.assertNotEqual(source.image.name, clone.image.name)
            self.assertTrue(source.image.storage.exists(source.image.name))
            self.assertTrue(clone.image.storage.exists(clone.image.name))
            with self.captureOnCommitCallbacks(execute=True):
                clone.image = ""
                clone.save()
            self.assertTrue(source.image.storage.exists(source.image.name))

    def test_copy_token_cannot_be_tampered_or_used_by_another_administrator(self):
        response = self.client.post(self.url, self.data)
        location = response["Location"]
        for target in (location + "bad",):
            self.assertEqual(self.client.get(target).context["adminform"].form["name"].value(), None)
        self.client.force_login(get_user_model().objects.create_superuser("other-admin", "", "qa-only"))
        self.assertEqual(self.client.get(location).context["adminform"].form["name"].value(), None)


class PresentationMigrationTests(TransactionTestCase):
    def test_migration_preserves_identity_units_prices_images_and_accepts_legacy_edit(self):
        old = [("catalog", "0004_opening_hours")]
        current = [("catalog", "0008_integer_prices")]
        executor = MigrationExecutor(connection)
        executor.migrate(old)
        try:
            apps = executor.loader.project_state(old).apps
            category = apps.get_model("catalog", "Category").objects.create(name="Old QA", slug="old-qa")
            model = apps.get_model("catalog", "Product")
            for unit, step in (("kg", "0.10"), ("unidad", "2"), ("paquete", "3")):
                model.objects.create(category=category, name="Old " + unit, brand="QA", description="Original",
                                     sale_unit=unit, quantity_step=step, retail_price="123.45", wholesale_price="100.50",
                                     image="products/original.webp", is_active=False)
            before = list(model.objects.order_by("pk").values())
            executor = MigrationExecutor(connection)
            executor.migrate(current)
            after = list(Product.objects.order_by("pk").values())
            self.assertEqual(len(before), len(after))
            for previous, product in zip(before, after):
                self.assertEqual(product.pop("quantity_step"), Decimal("1"))
                previous.pop("quantity_step")
                for name in ("retail_price", "wholesale_price"):
                    self.assertEqual(product[name], int(previous[name]))
                    previous[name] = product[name]
                self.assertEqual(product, previous)
            legacy = Product.objects.get(sale_unit="unidad")
            form = ProductAdminForm(instance=legacy)
            self.assertIn(("unidad", "unidad (anterior)"), form.fields["sale_unit"].choices)
            legacy.name = "Edited legacy"
            legacy.full_clean(exclude=["image"])
            legacy.save()
            with self.assertRaises(ValidationError):
                Product(category_id=category.pk, name="New legacy", sale_unit="unidad", retail_price="1").save()
        finally:
            MigrationExecutor(connection).migrate([("catalog", "0009_whatsapp_readable_format")])
