import json
from urllib.parse import parse_qs, urlparse

from django.test import TestCase, override_settings
from django.urls import reverse

from .cart import calculate_cart, product_revision
from .models import Category, Product
from .whatsapp import PRICE_WARNING, whatsapp_message, whatsapp_url


@override_settings(WHATSAPP_PHONE="5491100000000")  # Sólo fixture: nunca se navega ni envía.
class WhatsAppTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(category=category, name="Chocolate & test", brand="Marca test", retail_price="100.25", wholesale_price="90.50", sale_unit="kg", quantity_step="0.1")
        self.product.refresh_from_db()

    def item(self):
        return {"id": self.product.pk, "quantity": "0.3", "price_type": "wholesale", "sale_unit": "kg", "revision": product_revision(self.product)}

    def post(self, endpoint, items=None, **data):
        return self.client.post(reverse(endpoint), {"items": json.dumps([self.item()] if items is None else items), **data})

    def test_message_has_current_selection_and_encoded_complete_text(self):
        message = whatsapp_message(calculate_cart([self.item()]))
        for expected in ("Marca Marca test", "precio mayorista $ 90,50/kg", "cantidad 0,3 kg", "subtotal estimado: $ 27,15", "Total estimado: $ 27,15", PRICE_WARNING):
            self.assertIn(expected, message)
        url = whatsapp_url(message)
        self.assertEqual(urlparse(url).netloc, "wa.me")
        self.assertEqual(parse_qs(urlparse(url).query)["text"], [message])

    def test_brand_omitted_and_long_messages_not_truncated(self):
        self.product.brand = ""
        self.product.name = "Producto " + "á" * 150
        self.product.save()
        cart = calculate_cart([self.item()])
        message = whatsapp_message({**cart, "rows": cart["rows"] * 100})
        self.assertNotIn(" - Marca ", message)
        self.assertEqual(message.count("- Producto"), 100)
        self.assertEqual(parse_qs(urlparse(whatsapp_url(message)).query)["text"][0], message)

    def test_review_has_warning_and_cancel_without_ready_link(self):
        response = self.post("cart_review")
        self.assertContains(response, PRICE_WARNING)
        self.assertContains(response, "Volver al carrito")
        self.assertContains(response, "Continuar a WhatsApp")
        self.assertNotContains(response, 'id="whatsapp-ready"')
        self.assertNotContains(self.post("cart_whatsapp"), 'id="whatsapp-ready"')

    def test_acceptance_generates_link_only_after_revalidation(self):
        response = self.post("cart_whatsapp", accepted="yes")
        self.assertContains(response, 'id="whatsapp-ready"')
        item = self.item()
        Product.objects.filter(pk=self.product.pk).update(wholesale_price="120.00")
        response = self.post("cart_whatsapp", [item], accepted="yes")
        self.assertNotContains(response, 'id="whatsapp-ready"')
        self.assertContains(response, "$ 36,00")
        revised = response.context["cart"]["items"]
        self.assertContains(self.post("cart_whatsapp", revised, accepted="yes"), 'id="whatsapp-ready"')

    def test_removed_invalid_empty_or_missing_phone_prevent_navigation(self):
        self.product.is_active = False
        self.product.save()
        self.assertNotContains(self.post("cart_whatsapp", accepted="yes"), 'id="whatsapp-ready"')
        self.assertNotContains(self.post("cart_whatsapp", [], accepted="yes"), 'id="whatsapp-ready"')
        self.product.is_active = True
        self.product.save()
        with override_settings(WHATSAPP_PHONE=""):
            response = self.post("cart_review")
            self.assertContains(response, "todavía no habilitó")
            self.assertNotContains(self.post("cart_whatsapp", accepted="yes"), 'id="whatsapp-ready"')
        self.assertEqual(self.client.get(reverse("cart_whatsapp")).status_code, 405)
