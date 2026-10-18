import json
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from .admin import ProductAdminForm
from .cart import calculate_cart
from .csv_import import preview_rows
from .models import BusinessSettings, Category, Product
from .templatetags.catalog_format import ars
from .test_csv_import import csv_row
from .whatsapp import whatsapp_message


class IntegerPriceTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Repostería", slug="reposteria")

    def test_admin_rejects_decimals_separators_exponents_and_symbols_in_both_prices(self):
        for name in ("retail_price", "wholesale_price"):
            for value in ("100.99", "100,99", "100.00", "1e3", "+100", "-1", "1 000", "$100"):
                with self.subTest(name=name, value=value):
                    form = ProductAdminForm(data={"category": self.category.pk, "name": "Chips", "sale_unit": "kg",
                                                  "retail_price": "100", "wholesale_price": "90", name: value})
                    self.assertFalse(form.is_valid())
                    self.assertIn(name, form.errors)
        form = ProductAdminForm(data={"category": self.category.pk, "name": "Chips", "sale_unit": "kg",
                                      "retail_price": "100", "wholesale_price": "0"})
        self.assertTrue(form.is_valid(), form.errors)
        product = form.save()
        self.assertEqual((product.retail_price, product.wholesale_price), (100, 0))

    def test_model_save_and_validation_do_not_silently_round_fractional_prices(self):
        for name in ("retail_price", "wholesale_price"):
            for value in ("0.99", "100.01", "100.99"):
                with self.subTest(name=name, value=value):
                    product = Product(category=self.category, name="Chips", retail_price="100")
                    setattr(product, name, Decimal(value))
                    with self.assertRaises(ValidationError):
                        product.full_clean()
                    with self.assertRaises(ValidationError):
                        product.save()
        self.assertEqual(Product.objects.count(), 0)

    def test_csv_rejects_even_zero_decimals_and_large_prices_roundtrip(self):
        for index in (6, 7):
            for value in ("100.00", "100,00", "100.99", "100,99"):
                preview = preview_rows([{"number": 2, "values": csv_row(**{f"column{index}": value})}])
                self.assertEqual(preview.error_count, 1)
        preview = preview_rows([{"number": 2, "values": csv_row(column6="999999999999")}])
        self.assertEqual(preview.error_count, 0)
        self.assertEqual(ars(preview.rows[0].product.retail_price), "$ 999.999.999.999")

    def test_catalog_cart_message_and_formatter_use_whole_pesos(self):
        product = Product.objects.create(category=self.category, name="Chips", retail_price="100", wholesale_price="90")
        item = {"id": product.pk, "quantity": "3", "price_type": "retail"}
        cart = calculate_cart([item])
        self.assertEqual(cart["total"], 300)
        self.assertEqual(cart["rows"][0]["subtotal"], 300)
        self.assertIn("$ 300", whatsapp_message(cart))
        self.assertNotIn(",00", whatsapp_message(cart))
        self.assertContains(self.client.get(reverse("home")), "$ 100")
        self.assertNotContains(self.client.get(reverse("home")), "$ 100,00")
        self.assertEqual(ars("100.99"), "$ 100")
        self.assertEqual(ars("0.99"), "$ 0")

    def test_all_cart_diagnostics_are_out_of_visual_flow_but_prevent_review(self):
        product = Product.objects.create(category=self.category, name="Chips", retail_price="100")
        items = [{"id": product.pk, "quantity": "3.3", "price_type": "wholesale"},
                 {"id": 999999, "quantity": "1", "price_type": "retail"}]
        response = self.client.post(reverse("cart_refresh"), {"items": json.dumps(items)})
        self.assertContains(response, 'id="cart-notices" class="visually-hidden"')
        self.assertContains(response, 'class="visually-hidden" data-cart-error')
        self.assertContains(response, 'aria-invalid="true"')
        self.assertContains(response, 'id="cart-review" disabled')
        self.assertContains(response, 'type="text" inputmode="numeric" pattern="[0-9]+" maxlength="7" data-digits-only')


class IntegerPriceMigrationTests(TransactionTestCase):
    def test_truncates_before_altering_precision_and_preserves_all_other_data(self):
        old = [("catalog", "0007_whatsapp_subtotal_label")]
        current = [("catalog", "0008_integer_prices")]
        MigrationExecutor(connection).migrate(old)
        try:
            apps = MigrationExecutor(connection).loader.project_state(old).apps
            category = apps.get_model("catalog", "Category").objects.create(name="Anterior", slug="anterior")
            historical = apps.get_model("catalog", "Product")
            for retail, wholesale in (("100.99", "90.50"), ("0.99", None), ("9999999999.99", "0.01"), ("123.00", "99.00")):
                historical.objects.create(category=category, name="Mismo título", description="Presentación original",
                    retail_price=retail, wholesale_price=wholesale, image="products/original.webp")
            business = BusinessSettings.objects.create(address="Dirección conservada")
            before_business = BusinessSettings.objects.values().get(pk=business.pk)
            before = list(historical.objects.order_by("pk").values())
            MigrationExecutor(connection).migrate(current)
            after = list(Product.objects.order_by("pk").values())
            for previous, product in zip(before, after):
                for name in ("retail_price", "wholesale_price"):
                    previous[name] = int(previous[name]) if previous[name] is not None else None
                self.assertEqual(previous, product)
            self.assertEqual(BusinessSettings.objects.values().get(), before_business)
            self.assertEqual([p["retail_price"] for p in after], [100, 0, 9999999999, 123])
        finally:
            MigrationExecutor(connection).migrate([("catalog", "0009_whatsapp_readable_format")])
