import json
from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from .cart import calculate_cart, parse_items, product_revision
from .models import Category, Product


class CartTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(category=self.category, name="Test", sale_unit="kg", quantity_step="1", retail_price="10", wholesale_price="9")
        self.product.refresh_from_db()

    def item(self, **changes):
        return {"id": self.product.pk, "quantity": "1", "price_type": "retail", "revision": product_revision(self.product), "sale_unit": "kg", **changes}

    def test_quantity_errors_are_floating_only_but_still_block_invalid_amounts(self):
        cases = (("-2", "No se pueden ingresar valores negativos"),
                 ("0", "Ingresá una cantidad de al menos 1."),
                 ("3.3", "Solo se permiten cantidades enteras, sin decimales."))
        for quantity, message in cases:
            with self.subTest(quantity=quantity):
                cart = calculate_cart([self.item(quantity=quantity)])
                self.assertFalse(cart["valid"])
                self.assertIsNone(cart["total"])
                self.assertEqual(cart["rows"][0]["quantity_error"], message)
                self.assertEqual(cart["rows"][0]["visible_errors"], [])
                response = self.client.post(reverse("cart_refresh"), {"items": json.dumps(cart["items"])})
                self.assertContains(response, 'class="visually-hidden" data-quantity-error >' + message)
                self.assertContains(response, 'aria-invalid="true"')
                self.assertContains(response, 'data-cart-error hidden')
        for quantity in ("1", "2", "1.00"):
            self.assertTrue(calculate_cart([self.item(quantity=quantity)])["valid"])

    def test_integer_price_and_total(self):
        cart = calculate_cart([self.item()])
        self.assertEqual(cart["total"], Decimal("10"))
        self.assertTrue(cart["valid"])

    def test_remove_button_has_product_name_and_accessible_missing_product_fallback(self):
        for identifier, label in ((self.product.pk, "Quitar Test del carrito"), (999999, "Quitar producto no disponible 999999 del carrito")):
            response = self.client.post(reverse("cart_refresh"), {"items": json.dumps([self.item(id=identifier)])})
            self.assertContains(response, f'aria-label="{label}"')
            self.assertContains(response, 'class="icon trash-icon"', count=1)
            self.assertContains(response, 'aria-hidden="true" focusable="false"')
            self.assertNotContains(response, ">Quitar</button>")

    def test_fresh_prices_override_any_local_price(self):
        item = self.item(price="1")
        Product.objects.filter(pk=self.product.pk).update(retail_price="20")
        cart = calculate_cart([item])
        self.assertEqual(cart["total"], Decimal("20"))
        self.assertTrue(cart["notices"])
        self.assertNotIn("price", cart["items"][0])

    def test_total_sums_exact_integer_subtotals(self):
        other = Product.objects.create(category=self.category, name="Otro test", sale_unit="kg", quantity_step="1", retail_price="10")
        other.refresh_from_db()
        cart = calculate_cart([self.item(), self.item(id=other.pk, revision=product_revision(other))])
        self.assertEqual(cart["total"], Decimal("20"))

    def test_missing_wholesale_uses_retail_but_inactive_and_deleted_prevent_total(self):
        self.product.wholesale_price = None
        self.product.save()
        cart = calculate_cart([self.item(price_type="wholesale")])
        self.assertTrue(cart["valid"])
        self.assertEqual(cart["total"], Decimal("10"))
        self.assertEqual(cart["items"][0]["price_type"], "retail")
        self.assertTrue(cart["notices"])
        self.product.is_active = False
        self.product.save()
        self.assertIsNone(calculate_cart([self.item()])["total"])
        self.product.delete()
        self.assertFalse(calculate_cart([self.item(id=999)])["valid"])

    def test_invalid_quantity_and_unit_change_require_correction(self):
        for amount in ("0", "-1", "0.15", "NaN", "1e2", "1.001"):
            self.assertFalse(calculate_cart([self.item(quantity=amount)])["valid"])
        self.product.sale_unit = "pack"
        self.product.quantity_step = Decimal("1")
        self.product.save()
        cart = calculate_cart([self.item(quantity="1", sale_unit="kg")])
        self.assertFalse(cart["valid"])
        self.assertEqual(cart["rows"][0]["quantity_value"], "")

    def test_inactive_category_and_empty_cart(self):
        self.category.is_active = False
        self.category.save()
        self.assertFalse(calculate_cart([self.item()])["valid"])
        self.assertFalse(calculate_cart([])["valid"])

    def test_refresh_is_post_html_and_not_cached(self):
        response = self.client.post(reverse("cart_refresh"), {"items": json.dumps([self.item()])})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "$ 10")
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.assertEqual(self.client.get(reverse("cart_refresh")).status_code, 405)

    def test_refresh_requires_csrf_and_rejects_bad_input(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse("cart_refresh"), {"items": "[]"}).status_code, 403)
        for data in ("bad", "{}", '[{"id": true}]', json.dumps([self.item(price_type={})]), json.dumps([self.item(), self.item()])):
            self.assertEqual(self.client.post(reverse("cart_refresh"), {"items": data}).status_code, 400)
        self.assertEqual(parse_items("[]"), [])

    def test_cart_photo_uses_current_product_and_is_not_persisted(self):
        response = self.client.post(reverse("cart_refresh"), {"items": json.dumps([self.item()])})
        self.assertNotContains(response, 'cart-thumbnail')
        self.product.image = "products/current.webp"
        self.product.save()
        response = self.client.post(reverse("cart_refresh"), {"items": json.dumps([self.item()])})
        self.assertContains(response, 'class="product-image-open cart-thumbnail"', count=1)
        self.assertContains(response, '/media/products/current.webp')
        self.assertNotIn("image", response.context["cart"]["items"][0])
        response = self.client.get(reverse("cart"))
        self.assertContains(response, 'id="product-image-dialog"', count=1)
        self.assertNotContains(response, "Vaciar carrito")
        self.assertNotContains(response, "Seguir viendo productos")
        self.assertContains(response, '<h1 class="visually-hidden">Revisá tu carrito.</h1>')

    def test_public_cart_only_uses_retail_without_tariff_or_brand_controls(self):
        self.product.wholesale_condition = "Condición específica de prueba"
        self.product.brand = "Marca privada de prueba"
        self.product.save()
        for price_type in ("retail", "wholesale"):
            response = self.client.post(reverse("cart_refresh"), {"items": json.dumps([self.item(price_type=price_type)])})
            self.assertContains(response, "$ 10")
            for text in ("Condición específica de prueba", "Marca privada de prueba", "Minorista", "Mayorista", "Tipo de precio", 'class="cart-price"'):
                self.assertNotContains(response, text)
            self.assertEqual(response.context["cart"]["items"][0]["price_type"], "retail")
        self.product.refresh_from_db()
        self.assertEqual(self.product.wholesale_price, Decimal("9"))
        self.assertEqual(self.product.wholesale_condition, "Condición específica de prueba")

    def test_wholesale_only_edits_do_not_change_public_revision(self):
        revision = product_revision(self.product)
        self.product.wholesale_price = "7"
        self.product.wholesale_condition = "Nueva condición interna"
        self.product.save()
        self.assertEqual(product_revision(self.product), revision)
        self.assertFalse(calculate_cart([self.item()])["notices"])

    def test_decrease_is_trash_at_one_and_minus_above_one(self):
        for quantity, remove in (("1", True), ("2", False), ("0.15", True)):
            cart = calculate_cart([self.item(quantity=quantity)])
            self.assertEqual(cart["rows"][0]["remove_on_decrease"], remove)
            response = self.client.post(reverse("cart_refresh"), {"items": json.dumps(cart["items"])})
            self.assertContains(response, f'data-remove="{str(remove).lower()}"')
            self.assertContains(response, 'class="quantity-adjust cart-adjust" data-direction="1"')
            self.assertNotContains(response, 'class="secondary remove-item"')
