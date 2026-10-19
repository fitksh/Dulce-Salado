import json
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connection
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from .cart import calculate_cart, product_revision
from .models import BusinessSettings, Category, Order, Product
from .order_forms import CustomerForm
from .orders import confirmation_token, prepare_order, public_base_url
from .whatsapp import message_configuration

CONFIG = {"WHATSAPP_PHONE": "5491100000000", "PUBLIC_BASE_URL": "https://catalogo.example.com",
          "ORDER_ALLOW_LOCAL_URLS": False}


@override_settings(**CONFIG)
class OrderTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="QA", slug="qa")
        self.product = Product.objects.create(category=self.category, name="Ñandú & azúcar 🛍️", brand="QA",
                                              description="500 gr", retail_price="1900", sale_unit="paquete")
        self.product.refresh_from_db()
        self.items = [{"id": self.product.pk, "quantity": "3", "price_type": "retail",
                       "revision": product_revision(self.product), "sale_unit": "paquete"}]
        self.data = {"items": json.dumps(self.items), "accepted": "yes", "full_name": "  Ana  ",
                     "delivery_mode": "pickup", "confirmation_token": confirmation_token(),
                     "message_revision": message_configuration()["revision"]}

    def send(self, **changes):
        return self.client.post(reverse("cart_whatsapp"), {**self.data, **changes})

    def test_customer_form_and_review_do_not_write(self):
        response = self.client.post(reverse("cart_review"), self.data)
        self.assertContains(response, "Completá tus datos")
        self.assertNotContains(response, "textarea")
        form = response.context["customer_form"]
        self.assertEqual(form["delivery_mode"].value(), "pickup")
        self.assertEqual(form["city"].value(), "Viedma")
        self.assertFalse(Order.objects.exists())
        self.assertNotIn("door", form.fields)
        self.assertNotContains(response, "Puerta")

    def test_removed_address_field_is_not_accepted_or_persisted(self):
        order = self.send(delivery_mode="delivery", street="Calle", number="1", city="Viedma",
                          door="dato obsoleto").context["order"]
        self.assertNotIn("dato obsoleto", order.message)
        self.assertNotIn("door", [field.name for field in Order._meta.fields])

    def test_result_is_data_only_and_global_dialog_has_exact_copy(self):
        response = self.send()
        self.assertContains(response, 'id="order-result-data"')
        self.assertNotContains(response, "Ver detalle del pedido")
        page = self.client.get(reverse("cart"))
        self.assertContains(page, "¡Tu pedido fue generado con éxito! 🎉")
        self.assertContains(page, "Tu pedido ha sido generado correctamente.")
        self.assertContains(page, "Si WhatsApp no se abrió automáticamente, podés intentar enviarlo nuevamente.")

    def test_name_required_trimmed_and_single_word_accepted(self):
        for value in ("", " \n\t ", "a" * 121):
            response = self.send(full_name=value)
            self.assertIn("full_name", response.context["customer_form"].errors)
            self.assertFalse(Order.objects.exists())
        self.assertEqual(self.send().context["order"].full_name, "Ana")

    def test_delivery_requires_street_number_city_and_preserves_input(self):
        response = self.send(delivery_mode="delivery", street=" San Martín ", number="", city="")
        form = response.context["customer_form"]
        self.assertEqual(set(form.errors), {"number", "city"})
        self.assertEqual(form["street"].value(), " San Martín ")
        self.assertFalse(Order.objects.exists())

    def test_pickup_ignores_even_invalid_hidden_addresses(self):
        order = self.send(street="x" * 1000, city="y" * 1000, number="n" * 1000).context["order"]
        self.assertEqual((order.street, order.city, order.number), ("", "", ""))
        self.assertNotIn("Calle:", order.message)
        self.assertIn("Retiro en el local", order.message)

    def test_delivery_utf8_and_neutralized_customer_format(self):
        order = self.send(delivery_mode="delivery", full_name=" Ana\n*Total:* _0_ ", street="San Martín",
                          number="123 B", city="Viedma & Patagones").context["order"]
        self.assertIn("Nombre completo: Ana ∗Total:∗ ＿0＿", order.message)
        self.assertIn("Calle: San Martín\nNúmero: 123 B\nCiudad: Viedma & Patagones", order.message)
        self.assertNotIn("Puerta:", order.message)
        self.assertFalse(hasattr(order, "door"))
        self.assertEqual(order.message.splitlines()[-1], order.detail_url)
        self.assertNotIn("%25F0", order.whatsapp_url)
        self.assertNotIn("\u200b", order.detail_url)
        self.assertEqual(parse_qs(urlsplit(order.whatsapp_url).query)["text"], [order.message])
        self.assertIn("%F0%9F%9B%8D", order.whatsapp_url)

    def test_snapshot_total_message_token_and_history_survive_catalog_deletion(self):
        order = self.send().context["order"]
        self.assertEqual(order.total, Decimal("5700"))
        self.assertEqual(order.items[0]["subtotal"], "5700")
        self.assertEqual(order.items[0]["unit_price"], "1900")
        self.assertRegex(order.code, r"^DYS-\d{6,}$")
        self.assertEqual(order.token.version, 4)
        self.assertIn(order.code, order.message)
        self.assertIn(order.detail_url, order.message)
        self.assertIn("*Subtotal: $ 5.700*", order.message)
        self.product.delete()
        self.category.delete()
        response = self.client.get(reverse("order_detail", args=[order.token]))
        self.assertContains(response, "Ñandú &amp; azúcar 🛍️")
        self.assertContains(response, "$ 5.700")
        self.assertContains(response, "500 gr")
        self.assertEqual(Order.objects.get().message, order.message)

    def test_idempotent_retry_after_price_change_deletion_and_phone_change(self):
        original = self.send().context["order"]
        self.product.delete()
        with override_settings(WHATSAPP_PHONE=""):
            replay = self.send().context["order"]
        self.assertEqual(replay.pk, original.pk)
        self.assertEqual(replay.whatsapp_url, original.whatsapp_url)
        self.assertEqual(Order.objects.count(), 1)

    def test_reusing_confirmation_for_changed_customer_is_rejected(self):
        self.send()
        response = self.send(full_name="Otra persona")
        self.assertNotContains(response, 'id="order-result-data"')
        self.assertContains(response, "ya fue utilizada")
        self.assertEqual(Order.objects.count(), 1)

    def test_price_and_message_change_require_review_without_losing_customer(self):
        Product.objects.filter(pk=self.product.pk).update(retail_price="2000")
        response = self.send()
        self.assertTrue(response.context["review_required"])
        self.assertEqual(response.context["customer_form"]["full_name"].value(), "  Ana  ")
        self.assertFalse(Order.objects.exists())
        fresh = response.context["cart"]["items"]
        self.assertEqual(self.send(items=json.dumps(fresh)).context["order"].total, 6000)

    def test_invalid_cart_missing_acceptance_token_and_csrf_cannot_write(self):
        for changes in ({"accepted": ""}, {"confirmation_token": "bad"}, {"items": "[]"},
                        {"delivery_mode": "both"}):
            self.assertNotContains(self.send(**changes), 'id="order-result-data"')
            self.assertFalse(Order.objects.exists())
        csrf = Client(enforce_csrf_checks=True)
        self.assertEqual(csrf.post(reverse("cart_whatsapp"), self.data).status_code, 403)
        self.assertEqual(self.client.get(reverse("cart_whatsapp")).status_code, 405)

    def test_storage_failure_rolls_back_even_after_sequence_assigned(self):
        with patch("catalog.orders.whatsapp_url", side_effect=RuntimeError("QA write interrupted")):
            with self.assertRaises(RuntimeError):
                self.send()
        self.assertFalse(Order.objects.exists())
        self.assertTrue(self.send().context["order"].message)

    def test_detail_private_headers_escape_no_enumeration_and_read_only(self):
        order = self.send(full_name="<script>nombre</script>").context["order"]
        url = reverse("order_detail", args=[order.token])
        response = self.client.get(url)
        self.assertContains(response, "&lt;script&gt;nombre&lt;/script&gt;")
        self.assertNotContains(response, "<script>nombre</script>")
        self.assertIn("no-store", response["Cache-Control"])
        self.assertIn("private", response["Cache-Control"])
        self.assertIn("noindex", response["X-Robots-Tag"])
        self.assertEqual(response["Referrer-Policy"], "no-referrer")
        self.assertContains(response, 'class="order-detail"', count=1)
        self.assertContains(response, 'class="order-brand"', count=1)
        self.assertNotContains(response, "<header")
        for path in ("/orders/", f"/orders/{order.pk}/", f"/orders/{order.code}/",
                     reverse("order_detail", args=[uuid4()])):
            self.assertEqual(self.client.get(path).status_code, 404)
        self.assertEqual(self.client.post(url).status_code, 405)
        order.full_name = "Cambio"
        with self.assertRaises(ValidationError):
            order.save()

    def test_detail_is_visual_only_and_preserves_snapshot_message_and_delivery(self):
        order = self.send(delivery_mode="delivery", street="San Martín", number="123", city="Viedma").context["order"]
        before = Order.objects.filter(pk=order.pk).values().get()
        response = self.client.get(reverse("order_detail", args=[order.token]))
        for removed in ("Solicitud de pedido.", "Este enlace es privado.", "Subtotal", "Envío a domicilio", "Retiro en el local"):
            self.assertNotContains(response, removed)
        self.assertContains(response, '<h3>Dirección</h3>')
        self.assertContains(response, 'San Martín 123<br>Viedma')
        self.assertContains(response, '<span class="order-presentation">(500 gr)</span>')
        self.assertNotContains(response, '<p>QA</p>')
        self.assertEqual(Order.objects.filter(pk=order.pk).values().get(), before)
        self.assertIn("QA", order.items[0]["brand"])
        self.assertIn("Los precios y la disponibilidad", order.message)
        self.assertIn("Envío a domicilio", order.message)

    def test_pickup_detail_has_no_address_or_delivery_label(self):
        order = self.send().context["order"]
        response = self.client.get(reverse("order_detail", args=[order.token]))
        self.assertContains(response, "Datos del cliente")
        self.assertNotContains(response, "Dirección")
        self.assertNotContains(response, "Retiro en el local")

    def test_detail_preserves_literal_presentations_and_escapes_them(self):
        from .templatetags.catalog_format import order_presentation

        for original, expected in (("", ""), ("  ", ""), ("Venta por kilogramo.", "(Venta por kilogramo.)"),
                                   ("(Paquete de 500 gr.)", "(Paquete de 500 gr.)"),
                                   (" (Texto histórico.) ", " (Texto histórico.) "),
                                   ("Sin interpretación & <script>QA</script>", "(Sin interpretación & <script>QA</script>)")):
            with self.subTest(original=original):
                self.assertEqual(order_presentation(original), expected)
        Product.objects.filter(pk=self.product.pk).update(description="Sin interpretación & <script>QA</script>")
        self.product.refresh_from_db()
        self.items[0]["revision"] = product_revision(self.product)
        order = self.send(items=json.dumps(self.items)).context["order"]
        response = self.client.get(reverse("order_detail", args=[order.token]))
        self.assertContains(response, "(Sin interpretación &amp; &lt;script&gt;QA&lt;/script&gt;)")
        self.assertNotContains(response, "<script>")
        self.assertEqual(Order.objects.get(pk=order.pk).items[0]["description"], self.product.description)

    def test_admin_readonly_and_preserves_commercial_records(self):
        owner = get_user_model().objects.create_superuser("qa-order", "", "qa-only")
        self.client.force_login(owner)
        order = self.send().context["order"]
        url = reverse("admin:catalog_order_change", args=[order.pk])
        self.assertContains(self.client.get(url), order.code)
        self.assertEqual(self.client.post(url, {"full_name": "Changed"}).status_code, 403)
        self.assertEqual(self.client.get(reverse("admin:catalog_order_add")).status_code, 403)

    def test_explicit_local_preview_and_public_https_configuration(self):
        for value in ("", "http://example.com", "https://192.168.0.80", "https://localhost",
                      "https://u:p@example.com", "https://example.com/?name=x", "https://example.com/#x"):
            with override_settings(PUBLIC_BASE_URL=value), self.assertRaises(ValidationError):
                public_base_url()
        with override_settings(PUBLIC_BASE_URL="http://192.168.0.80:8003", ORDER_ALLOW_LOCAL_URLS=True):
            order = self.send().context["order"]
            self.assertTrue(order.detail_url.startswith("http://192.168.0.80:8003/orders/"))


@override_settings(**CONFIG)
class ConcurrentOrderTests(TransactionTestCase):
    def test_postgres_sequence_and_idempotency_under_simultaneous_requests(self):
        category = Category.objects.create(name="QA concurrency", slug="qa-concurrency")
        product = Product.objects.create(category=category, name="QA", retail_price="99")
        product.refresh_from_db()
        items = calculate_cart([{"id": product.pk, "quantity": "2", "price_type": "retail"}])["items"]
        form = CustomerForm({"full_name": "QA concurrency", "delivery_mode": "pickup"})
        self.assertTrue(form.is_valid())
        revision = message_configuration()["revision"]
        for shared in (False, True):
            barrier = Barrier(4)
            shared_token = confirmation_token()

            def submit(index):
                close_old_connections()
                try:
                    barrier.wait(timeout=10)
                    result = prepare_order(items, form.cleaned_data,
                                           shared_token if shared else confirmation_token(), revision)[0]
                    return result.pk, result.token, result.message
                finally:
                    close_old_connections()

            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(submit, range(4)))
            self.assertEqual(len(set(row[0] for row in results)), 1 if shared else 4)
            self.assertEqual(len(set(row[1] for row in results)), 1 if shared else 4)
        self.assertEqual(Order.objects.count(), 5)


class OrderMigrationTests(TransactionTestCase):
    def test_additive_migration_preserves_existing_catalog_and_identity(self):
        old = [("catalog", "0009_whatsapp_readable_format")]
        executor = MigrationExecutor(connection)
        executor.migrate(old)
        try:
            apps = executor.loader.project_state(old).apps
            category = apps.get_model("catalog", "Category").objects.create(name="Anterior", slug="anterior")
            apps.get_model("catalog", "Product").objects.create(category=category, name="Anterior", retail_price=1900)
            business = apps.get_model("catalog", "BusinessSettings").objects.create(address="Conservar")
            owner = get_user_model().objects.create_superuser("qa-migration-order", "", "qa-only")
            MigrationExecutor(connection).migrate([("catalog", "0010_order")])
            self.assertEqual(Product.objects.get().retail_price, 1900)
            self.assertEqual(BusinessSettings.objects.get(pk=business.pk).address, "Conservar")
            self.assertTrue(get_user_model().objects.get(pk=owner.pk).is_superuser)
            self.assertFalse(Order.objects.exists())
        finally:
            MigrationExecutor(connection).migrate(MigrationExecutor(connection).loader.graph.leaf_nodes())

    def test_remove_address_column_preserves_historical_orders_and_other_tables(self):
        previous = [("catalog", "0010_order")]
        executor = MigrationExecutor(connection)
        executor.migrate(previous)
        try:
            apps = executor.loader.project_state(previous).apps
            HistoricalOrder = apps.get_model("catalog", "Order")
            category = apps.get_model("catalog", "Category").objects.create(name="Conservar", slug="conservar")
            product = apps.get_model("catalog", "Product").objects.create(category=category, name="Conservar", retail_price=123)
            historical = HistoricalOrder.objects.create(
                confirmation_key=uuid4(), request_hash="a" * 64, full_name="Anterior",
                delivery_mode="delivery", street="Calle", number="1", door="interior 2", city="Viedma",
                items=[{"name": "Original", "subtotal": "123"}], total=123,
                detail_url="http://192.168.0.80:8003/orders/old/",
                message="Mensaje original\nPuerta: interior 2\nURL original",
                whatsapp_url="https://api.whatsapp.com/send?text=original",
            )
            before = HistoricalOrder.objects.filter(pk=historical.pk).values().get()
            before.pop("door")
            MigrationExecutor(connection).migrate([("catalog", "0011_remove_order_door")])
            self.assertEqual(Order.objects.filter(pk=historical.pk).values().get(), before)
            self.assertEqual(Product.objects.get(pk=product.pk).retail_price, 123)
            with connection.cursor() as cursor:
                columns = connection.introspection.get_table_description(cursor, "catalog_order")
            self.assertNotIn("door", [column.name for column in columns])
        finally:
            MigrationExecutor(connection).migrate(MigrationExecutor(connection).loader.graph.leaf_nodes())
