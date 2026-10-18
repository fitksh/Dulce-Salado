import json
from urllib.parse import parse_qs, urlparse

from django.test import TestCase, override_settings
from django.urls import reverse

from .cart import calculate_cart, product_revision
from .models import Category, Product
from .orders import confirmation_token
from .whatsapp import (
    PRICE_WARNING,
    SEPARATOR,
    message_configuration,
    whatsapp_message,
    whatsapp_url,
)


@override_settings(WHATSAPP_PHONE="5491100000000", PUBLIC_BASE_URL="https://catalogo.example.com", ORDER_ALLOW_LOCAL_URLS=False)  # Sólo fixture: nunca se navega ni envía.
class WhatsAppTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(category=category, name="Chocolate & test", brand="Marca test", retail_price="100", wholesale_price="90", sale_unit="kg", quantity_step="1")
        self.product.refresh_from_db()

    def item(self):
        return {"id": self.product.pk, "quantity": "3", "price_type": "retail", "sale_unit": "kg", "revision": product_revision(self.product)}

    def post(self, endpoint, items=None, **data):
        return self.client.post(reverse(endpoint), {"full_name": "Ana", "delivery_mode": "pickup", "confirmation_token": confirmation_token(), "items": json.dumps([self.item()] if items is None else items), "message_revision": message_configuration()["revision"], **data})

    def test_review_has_customer_form_without_message_or_copy(self):
        response = self.post("cart_review")
        self.assertContains(response, "Completá tus datos")
        self.assertContains(response, 'name="full_name"')
        self.assertNotContains(response, "textarea")
        self.assertNotContains(response, "copy-message")
        self.assertContains(response, 'id="review-cancel">Cancelar</button>')
        self.assertContains(response, ">Enviar</button>")

    def test_message_has_current_selection_and_encoded_complete_text(self):
        message = whatsapp_message(calculate_cart([self.item()]))
        self.assertEqual(message, "\n".join([
            "Hola! Quisiera realizar el siguiente pedido 🛍️:", "", "*1. Chocolate & test*",
            "Marca: Marca test", "Cantidad: 3 kg", "Precio: $ 100 por kg",
            "*Subtotal: $ 300*", "", SEPARATOR, "", "*💰 Total: $ 300*",
            "", PRICE_WARNING,
        ]))
        url = whatsapp_url(message)
        self.assertEqual(urlparse(url).netloc, "api.whatsapp.com")
        self.assertEqual(urlparse(url).path, "/send")
        self.assertEqual(parse_qs(urlparse(url).query)["phone"], ["5491100000000"])
        self.assertEqual(parse_qs(urlparse(url).query)["text"], [message])

    def test_brand_omitted_and_long_messages_not_truncated(self):
        self.product.brand = ""
        self.product.name = "Producto " + "á" * 150
        self.product.save()
        cart = calculate_cart([self.item()])
        message = whatsapp_message({**cart, "rows": cart["rows"] * 100})
        self.assertNotIn("Marca:", message)
        self.assertEqual(message.count(self.product.name), 100)
        self.assertEqual(message.count(SEPARATOR), 1)
        self.assertIn(f"100. {self.product.name}", message)
        self.assertEqual(parse_qs(urlparse(whatsapp_url(message)).query)["text"][0], message)

    def test_multiple_products_keep_order_units_tariffs_and_blank_brand_is_omitted(self):
        unit = Product.objects.create(category=self.product.category, name="Manga", brand="   ", sale_unit="pack",
                                      retail_price="650", wholesale_price="600", quantity_step="1")
        package = Product.objects.create(category=self.product.category, name="Velas", brand="Marca Paquete",
                                         sale_unit="paquete", retail_price="1200", wholesale_price="1000", quantity_step="1")
        items = [self.item(), {"id": unit.pk, "quantity": "2", "price_type": "retail"},
                 {"id": package.pk, "quantity": "3", "price_type": "wholesale"}]
        cart = calculate_cart(items)
        message = whatsapp_message(cart)
        self.assertEqual(message.count(SEPARATOR), 1)
        first, second, third = message.split("\n\n")[1:4]
        total = message.split(f"\n\n{SEPARATOR}\n\n")[1]
        self.assertIn("1. Chocolate & test", first)
        self.assertIn("2. Manga", second)
        self.assertNotIn("Marca:", second)
        self.assertIn("Cantidad: 2 packs\nPrecio: $ 650 por pack\n*Subtotal: $ 1.300*", second)
        self.assertIn("3. Velas*\nMarca: Marca Paquete", third)
        self.assertIn("Cantidad: 3 paquetes\nPrecio: $ 1.200 por paquete\n*Subtotal: $ 3.600*", third)
        self.assertTrue(total.startswith("*💰 Total: $ 5.200*"))
        self.assertEqual(message.count(PRICE_WARNING), 1)
        self.assertNotIn("**", message)
        self.assertEqual(parse_qs(urlparse(whatsapp_url(message)).query)["text"], [message])

    def test_special_characters_are_literal_without_changing_stored_names_or_brand(self):
        name = "Chocolate *premium* _50%_ & ñ + ~dulce~ `test`\nsegunda línea"
        brand = "Marca *Águila*\r\n_Artesanal_ ~A+B~ `99%`"
        self.product.name, self.product.brand = name, brand
        self.product.save()
        message = whatsapp_message(calculate_cart([self.item()]))
        self.assertIn("1. Chocolate ∗premium∗ ＿50%＿ & ñ + ∼dulce∼ ˋtestˋ segunda línea", message)
        self.assertIn("Marca: Marca ∗Águila∗ ＿Artesanal＿ ∼A+B∼ ˋ99%ˋ", message)
        self.assertEqual(message.count("*"), 6)  # Los datos no abren estilos; sólo el formato elegido por Admin.
        self.assertEqual(parse_qs(urlparse(whatsapp_url(message)).query)["text"], [message])
        self.product.refresh_from_db()
        self.assertEqual((self.product.name, self.product.brand), (name, brand))

    def test_ready_link_contains_saved_message_and_current_body(self):
        ready = self.post("cart_whatsapp", accepted="yes")
        order = ready.context["order"]
        self.assertIn(whatsapp_message(calculate_cart([self.item()])), order.message)
        self.assertEqual(parse_qs(urlparse(order.whatsapp_url).query)["text"], [order.message])

    def test_review_explains_confirmation_and_cancel_without_ready_link(self):
        response = self.post("cart_review")
        self.assertContains(response, "sujetos a confirmación del comercio")
        self.assertNotContains(response, 'id="order-result-data"')
        self.assertNotContains(self.post("cart_whatsapp"), 'id="order-result-data"')
        self.assertContains(response, '<h2 id="review-title" tabindex="-1">Completá tus datos</h2>')

    def test_acceptance_generates_link_only_after_revalidation(self):
        response = self.post("cart_whatsapp", accepted="yes")
        self.assertContains(response, 'id="order-result-data"')
        self.assertContains(self.client.get(reverse("cart")), 'target="_blank" rel="noopener noreferrer"')
        item = self.item()
        Product.objects.filter(pk=self.product.pk).update(retail_price="120")
        response = self.post("cart_whatsapp", [item], accepted="yes")
        self.assertNotContains(response, 'id="order-result-data"')
        self.assertEqual(response.context["cart"]["total"], 360)
        revised = response.context["cart"]["items"]
        self.assertContains(self.post("cart_whatsapp", revised, accepted="yes"), 'id="order-result-data"')

    def test_legacy_wholesale_requires_review_even_with_current_revision(self):
        item = {**self.item(), "price_type": "wholesale"}
        response = self.post("cart_whatsapp", [item], accepted="yes")
        self.assertNotContains(response, 'id="order-result-data"')
        self.assertContains(response, "el carrito ahora utiliza el precio publicado")
        self.assertEqual(response.context["cart"]["total"], 300)
        self.assertNotContains(response, "Precio mayorista:")
        revised = response.context["cart"]["items"]
        self.assertEqual(revised[0]["price_type"], "retail")
        self.assertContains(self.post("cart_whatsapp", revised, accepted="yes"), 'id="order-result-data"')

    def test_removed_invalid_empty_or_missing_phone_prevent_navigation(self):
        self.product.is_active = False
        self.product.save()
        self.assertNotContains(self.post("cart_whatsapp", accepted="yes"), 'id="order-result-data"')
        self.assertNotContains(self.post("cart_whatsapp", [], accepted="yes"), 'id="order-result-data"')
        self.product.is_active = True
        self.product.save()
        with override_settings(WHATSAPP_PHONE=""):
            response = self.post("cart_review")
            self.assertContains(response, "todavía no habilitó")
            self.assertNotContains(self.post("cart_whatsapp", accepted="yes"), 'id="order-result-data"')
        self.assertEqual(self.client.get(reverse("cart_whatsapp")).status_code, 405)
