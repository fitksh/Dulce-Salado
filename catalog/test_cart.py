import json
from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from .cart import calculate_cart, parse_items, product_revision
from .models import Category, Product


class CartTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(category=self.category, name="Test", sale_unit="kg", quantity_step="0.1", retail_price="10.25", wholesale_price="9.10")
        self.product.refresh_from_db()

    def item(self, **changes):
        return {"id": self.product.pk, "quantity": "0.1", "price_type": "retail", "revision": product_revision(self.product), "sale_unit": "kg", **changes}

    def test_decimal_rounding_and_sum(self):
        cart = calculate_cart([self.item()])
        self.assertEqual(cart["total"], Decimal("1.03"))
        self.assertTrue(cart["valid"])

    def test_fresh_prices_override_any_local_price(self):
        item = self.item(price="1")
        Product.objects.filter(pk=self.product.pk).update(retail_price="20.50")
        cart = calculate_cart([item])
        self.assertEqual(cart["total"], Decimal("2.05"))
        self.assertTrue(cart["notices"])
        self.assertNotIn("price", cart["items"][0])

    def test_total_sums_individually_rounded_subtotals(self):
        other = Product.objects.create(category=self.category, name="Otro test", sale_unit="kg", quantity_step="0.1", retail_price="10.25")
        other.refresh_from_db()
        cart = calculate_cart([self.item(), self.item(id=other.pk, revision=product_revision(other))])
        self.assertEqual(cart["total"], Decimal("2.06"))

    def test_missing_wholesale_inactive_and_deleted_prevent_total(self):
        self.product.wholesale_price = None
        self.product.save()
        self.assertFalse(calculate_cart([self.item(price_type="wholesale")])["valid"])
        self.product.is_active = False
        self.product.save()
        self.assertIsNone(calculate_cart([self.item()])["total"])
        self.product.delete()
        self.assertFalse(calculate_cart([self.item(id=999)])["valid"])

    def test_invalid_quantity_and_unit_change_require_correction(self):
        for amount in ("0", "-1", "0.15", "NaN", "1e2", "1.001"):
            self.assertFalse(calculate_cart([self.item(quantity=amount)])["valid"])
        self.product.sale_unit = "unidad"
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
        self.assertContains(response, "$ 1,03")
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

    def test_specific_wholesale_condition_only_for_selected_wholesale(self):
        self.product.wholesale_condition = "Condición específica de prueba"
        self.product.save()
        for price_type, expected in (("retail", False), ("wholesale", True)):
            response = self.client.post(reverse("cart_refresh"), {"items": json.dumps([self.item(price_type=price_type)])})
            if expected:
                self.assertContains(response, "Condición específica de prueba")
            else:
                self.assertNotContains(response, "Condición específica de prueba")
            self.assertNotContains(response, "Sujeto a confirmación comercial.")
        self.product.wholesale_condition = ""
        self.product.save()
        response = self.client.post(reverse("cart_refresh"), {"items": json.dumps([self.item(price_type="wholesale")])})
        self.assertNotContains(response, 'class="wholesale-note"')
