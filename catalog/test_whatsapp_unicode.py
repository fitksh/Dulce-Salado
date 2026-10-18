import json
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit

from django.test import TestCase, override_settings
from django.urls import reverse

from .cart import product_revision
from .models import BusinessSettings, Category, Product
from .orders import confirmation_token
from .whatsapp import message_configuration, whatsapp_url
from .whatsapp_templates import DEFAULT_MESSAGE_TEMPLATE


class ReadyLink(HTMLParser):
    href = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("id") == "whatsapp-ready":
            self.href = attrs["href"]


@override_settings(WHATSAPP_PHONE="5491100000000", PUBLIC_BASE_URL="https://catalogo.example.com", ORDER_ALLOW_LOCAL_URLS=False)
class WhatsAppUnicodeTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="QA", slug="qa")
        self.product = Product.objects.create(category=category, name="Chocolate", retail_price="100")

    def post(self, endpoint, **data):
        self.product.refresh_from_db()
        item = {"id": self.product.pk, "quantity": "3", "price_type": "retail",
                "revision": product_revision(self.product), "sale_unit": self.product.sale_unit}
        return self.client.post(reverse(endpoint), {"full_name": "Ana", "delivery_mode": "pickup", "confirmation_token": confirmation_token(), "items": json.dumps([item]),
            "message_revision": message_configuration()["revision"], **data})

    def test_direct_link_preserves_utf8_emoji_sequences_and_reserved_characters(self):
        message = "Hola 🛍️ 💰 📌 👩🏽‍🍳 👨‍👩‍👧‍👦 🇦🇷\nÑandú + azúcar & 50% #1? a=b / \"sí\""
        url = whatsapp_url(message)
        parsed = urlsplit(url)
        self.assertEqual((parsed.scheme, parsed.netloc, parsed.path), ("https", "api.whatsapp.com", "/send"))
        self.assertEqual(parse_qs(parsed.query), {"phone": ["5491100000000"], "text": [message]})
        self.assertEqual(parsed.fragment, "")
        self.assertIn("%F0%9F%9B%8D%EF%B8%8F", url)
        self.assertIn("%F0%9F%92%B0", url)
        self.assertIn("%F0%9F%93%8C", url)
        self.assertIn("%E2%80%8D", url)  # Unión de emoji compuesto.
        self.assertIn("%20", url)
        self.assertIn("%2B", url)
        self.assertNotIn("+", url)
        self.assertNotIn("%25F0", url)  # No codificar dos veces.
        self.assertNotIn("%EF%BF%BD", url)
        url.encode("ascii")

    def test_ready_html_link_keeps_the_exact_saved_unicode_message(self):
        BusinessSettings.objects.create(whatsapp_message_template=DEFAULT_MESSAGE_TEMPLATE + "\n📌 👩🏽‍🍳 🇦🇷")
        self.product.name = "Chocolate 🛍️ & ñ + 50%"
        self.product.brand = "Marca 🇦🇷"
        self.product.save()
        ready = self.post("cart_whatsapp", accepted="yes")
        order = ready.context["order"]
        message = order.message
        self.assertIn("🛍️", message)
        self.assertIn("💰", message)
        self.assertIn("👩🏽‍🍳 🇦🇷", message)
        parser = ReadyLink()
        parser.feed(ready.content.decode("utf-8"))
        parsed = urlsplit(parser.href)
        self.assertEqual(parsed.netloc, "api.whatsapp.com")
        self.assertEqual(parse_qs(parsed.query)["text"], [message])
        self.assertEqual(parser.href, order.whatsapp_url)
        self.assertNotIn("�", message)
