import importlib
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase

from .cart import calculate_cart
from .models import BusinessSettings, Category, Product
from .whatsapp import message_configuration, whatsapp_message
from .whatsapp_presentations import presentation_text
from .whatsapp_templates import (
    DEFAULT_MESSAGE_TEMPLATE,
    DEFAULT_PRODUCT_TEMPLATE,
    SEPARATOR,
    validate_product_template,
)


class WhatsAppPresentationTests(TestCase):
    def test_all_six_examples_same_titles_independent_presentations_and_exact_total(self):
        category = Category.objects.create(name="No mostrar categoría", slug="qa")
        examples = [
            ("Pasta de maní natural", "Entrenuts", "100 gr", "Porción de 100 gr.", "3", "800", "3 porciones de 100 g", "100 g", "2.400"),
            ("Chantilly en polvo", "Ledevit", "kg", "Venta por kilogramo.", "2", "14500", "2 kg", "kg", "29.000"),
            ("Crema de chocolate", "", "caja", "Caja de 5 kg.", "1", "60000", "1 caja de 5 kg", "caja", "60.000"),
            ("Crema de chocolate", "", "pack", "Pack de 3 paquetes de 500 gr.", "4", "18000", "4 packs de 3 paquetes de 500 g", "pack", "72.000"),
            ("Pasta de maní natural", "Entrenuts", "paquete", "Paquete de 500 gr.", "3", "4000", "3 paquetes de 500 g", "paquete", "12.000"),
            ("Crema de chocolate", "", "bolsa", "Bolsa de 2 kg.", "3", "24000", "3 bolsas de 2 kg", "bolsa", "72.000"),
        ]
        items = []
        for name, brand, unit, description, amount, price, *_ in examples:
            product = Product.objects.create(category=category, name=name, brand=brand, sale_unit=unit,
                description=description, retail_price=price)
            items.append({"id": product.pk, "quantity": amount, "price_type": "retail"})
        cart = calculate_cart(items)
        message = whatsapp_message(cart)
        self.assertEqual(cart["total"], Decimal("247400"))
        for index, example in enumerate(examples, 1):
            name, _, _, _, _, price, selected, unit_price, subtotal = example
            self.assertIn(f"*{index}. {name}*", message)
            self.assertIn(f"Cantidad: {selected}\nPrecio:", message)
            self.assertIn(" por " + unit_price, message)
            self.assertIn(f"*Subtotal: $ {subtotal}*", message)
        self.assertEqual(message.count("Marca:"), 3)
        self.assertEqual(message.count(SEPARATOR), 1)
        self.assertIn("*💰 Total: $ 247.400*", message)
        for unwanted in ("3 100 gr", "3 bolsa\n", "4 pack\n", "minorista", "mayorista", "estimado", "Presentación:", "No mostrar categoría"):
            self.assertNotIn(unwanted, message)
        self.assertTrue(message.endswith("📌 Los precios y la disponibilidad de los productos se confirmarán al procesar el pedido."))

    def test_singular_plural_and_legacy_unit_without_content(self):
        expected = {"100 gr": ("1 porción de 100 g", "3 porciones de 100 g"), "kg": ("1 kg", "3 kg"),
            "caja": ("1 caja", "3 cajas"), "pack": ("1 pack", "3 packs"), "paquete": ("1 paquete", "3 paquetes"),
            "bolsa": ("1 bolsa", "3 bolsas"), "unidad": ("1 unidad", "3 unidades")}
        for unit, labels in expected.items():
            for amount, label in zip((1, 3), labels):
                with self.subTest(unit=unit, amount=amount):
                    self.assertEqual(presentation_text(unit, "", Decimal(amount))["cantidad_presentacion"], label)

    def test_only_complete_known_content_forms_are_folded_into_quantity(self):
        for unit, description, expected in (
            ("caja", "CAJA de 5 KG.", "3 cajas de 5 kg"),
            ("paquete", "Paquete 500gr.", "3 paquetes de 500 g"),
            ("paquete", "500 gr", "3 paquetes de 500 g"),
            ("pack", "Pack de 3 paquetes de 500 g.", "3 packs de 3 paquetes de 500 g"),
            ("bolsa", "Bolsa de 0,5 kg.", "3 bolsas de 0,5 kg"),
        ):
            with self.subTest(description=description):
                result = presentation_text(unit, description, Decimal("3"))
                self.assertEqual(result["cantidad_presentacion"], expected)
                self.assertEqual(result["presentacion_adicional"], "")

    def test_free_text_and_ambiguous_content_are_preserved_without_guessing(self):
        for description in ("Caja individual para regalo.", "Caja de 5 kg o 10 kg.", "Contiene caja de 5 kg.", "Caja de 5 kg. Consultar sabor."):
            result = presentation_text("caja", description, Decimal("2"))
            self.assertEqual(result["cantidad_presentacion"], "2 cajas")
            self.assertEqual(result["presentacion_adicional"], description)

    def test_old_custom_fields_and_new_aliases_are_validated_without_losing_required_data(self):
        for template in (DEFAULT_PRODUCT_TEMPLATE, "{producto} {cantidad} {unidad} {precio} {subtotal}",
                         "{producto} {cantidad_presentacion} {precio} {subtotal}"):
            validate_product_template(template)
        for template in ("{producto} {precio} {subtotal}", "{producto} {cantidad} {precio} {subtotal}"):
            with self.assertRaises(ValidationError):
                validate_product_template(template)
        business = BusinessSettings.objects.create(whatsapp_product_template="{producto} {cantidad} {unidad} {precio} {subtotal}")
        self.assertEqual(message_configuration(business)["product"], business.whatsapp_product_template)


class WhatsAppFormatMigrationTests(TransactionTestCase):
    def check_migration(self, custom=False):
        old = [("catalog", "0008_integer_prices")]
        current = [("catalog", "0009_whatsapp_readable_format")]
        MigrationExecutor(connection).migrate(old)
        try:
            apps = MigrationExecutor(connection).loader.project_state(old).apps
            historical = apps.get_model("catalog", "BusinessSettings")
            business = historical.objects.create(address="Conservar dirección")
            if custom:
                business.whatsapp_message_template = "Hola propio 👋\n{productos}\nTotal {total}\nGracias"
                business.whatsapp_product_template = "{producto} {cantidad} {unidad} {precio} {subtotal}"
                business.save()
            before = historical.objects.values().get()
            category = Category.objects.create(name="Original", slug="original")
            Product.objects.create(category=category, name="No modificar", retail_price="100", description="Caja de 5 kg.", image="products/original.webp")
            products = list(Product.objects.values())
            MigrationExecutor(connection).migrate(current)
            after = BusinessSettings.objects.values().get()
            expected = dict(before)
            if not custom:
                expected.update(whatsapp_message_template=DEFAULT_MESSAGE_TEMPLATE, whatsapp_product_template=DEFAULT_PRODUCT_TEMPLATE)
            self.assertEqual(after, expected)
            self.assertEqual(list(Product.objects.values()), products)
            module = importlib.import_module("catalog.migrations.0009_whatsapp_readable_format")
            self.assertEqual(module.NEW_PRODUCT, DEFAULT_PRODUCT_TEMPLATE)
            self.assertEqual(module.NEW_MESSAGE, DEFAULT_MESSAGE_TEMPLATE)
        finally:
            MigrationExecutor(connection).migrate(MigrationExecutor(connection).loader.graph.leaf_nodes())

    def test_known_defaults_update_without_changing_products_or_other_settings(self):
        self.check_migration()

    def test_custom_text_is_not_overwritten(self):
        self.check_migration(custom=True)
