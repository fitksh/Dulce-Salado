import json
from urllib.parse import parse_qs, urlparse

from django.test import TestCase, override_settings
from django.urls import reverse

from .cart import calculate_cart, product_revision
from .models import Category, Product
from .whatsapp import PRICE_WARNING, SEPARATOR, whatsapp_message, whatsapp_url


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
        self.assertEqual(message, "\n".join([
            "Hola! Quisiera realizar el siguiente pedido:", "", "*1. Chocolate & test*",
            "- Marca: Marca test", "- Precio mayorista: $ 90,50/kg", "- Cantidad: 0,3 kg",
            "- *Subtotal estimado: $ 27,15*", "", SEPARATOR, "", "*TOTAL ESTIMADO: $ 27,15*",
            "", PRICE_WARNING, "", "Gracias, espero su respuesta!",
        ]))
        url = whatsapp_url(message)
        self.assertEqual(urlparse(url).netloc, "wa.me")
        self.assertEqual(parse_qs(urlparse(url).query)["text"], [message])

    def test_brand_omitted_and_long_messages_not_truncated(self):
        self.product.brand = ""
        self.product.name = "Producto " + "á" * 150
        self.product.save()
        cart = calculate_cart([self.item()])
        message = whatsapp_message({**cart, "rows": cart["rows"] * 100})
        self.assertNotIn("Marca:", message)
        self.assertEqual(message.count(self.product.name), 100)
        self.assertEqual(message.count(SEPARATOR), 100)
        self.assertIn(f"*100. {self.product.name}*", message)
        self.assertEqual(parse_qs(urlparse(whatsapp_url(message)).query)["text"][0], message)

    def test_multiple_products_keep_order_units_tariffs_and_blank_brand_is_omitted(self):
        unit = Product.objects.create(category=self.product.category, name="Manga", brand="   ", sale_unit="unidad",
                                      retail_price="650", wholesale_price="600", quantity_step="1")
        package = Product.objects.create(category=self.product.category, name="Velas", brand="Marca Paquete",
                                         sale_unit="paquete", retail_price="1200.50", wholesale_price="1000.25", quantity_step="1")
        items = [self.item(), {"id": unit.pk, "quantity": "2", "price_type": "retail"},
                 {"id": package.pk, "quantity": "3", "price_type": "wholesale"}]
        cart = calculate_cart(items)
        message = whatsapp_message(cart)
        self.assertEqual(message.count(SEPARATOR), 3)
        first, second, third, total = message.split(f"\n\n{SEPARATOR}\n\n")
        self.assertIn("*1. Chocolate & test*", first)
        self.assertIn("*2. Manga*", second)
        self.assertNotIn("Marca:", second)
        self.assertIn("- Precio minorista: $ 650,00/unidad\n- Cantidad: 2 unidad\n- *Subtotal estimado: $ 1.300,00*", second)
        self.assertIn("*3. Velas*\n- Marca: Marca Paquete", third)
        self.assertIn("- Precio mayorista: $ 1.000,25/paquete\n- Cantidad: 3 paquete\n- *Subtotal estimado: $ 3.000,75*", third)
        self.assertTrue(total.startswith("*TOTAL ESTIMADO: $ 4.327,90*"))
        self.assertEqual(message.count(PRICE_WARNING), 1)
        self.assertNotIn("**", message)
        self.assertEqual(parse_qs(urlparse(whatsapp_url(message)).query)["text"], [message])

    def test_special_characters_are_literal_without_changing_stored_names_or_brand(self):
        name = "Chocolate *premium* _50%_ & ñ + ~dulce~ `test`\nsegunda línea"
        brand = "Marca *Águila*\r\n_Artesanal_ ~A+B~ `99%`"
        self.product.name, self.product.brand = name, brand
        self.product.save()
        message = whatsapp_message(calculate_cart([self.item()]))
        self.assertIn("*1. Chocolate ∗premium∗ ＿50%＿ & ñ + ∼dulce∼ ˋtestˋ segunda línea*", message)
        self.assertIn("- Marca: Marca ∗Águila∗ ＿Artesanal＿ ∼A+B∼ ˋ99%ˋ", message)
        self.assertEqual(message.count("*"), 6)  # Título, subtotal y total: un par cada uno.
        self.assertEqual(parse_qs(urlparse(whatsapp_url(message)).query)["text"], [message])
        self.product.refresh_from_db()
        self.assertEqual((self.product.name, self.product.brand), (name, brand))

    def test_preview_and_ready_link_contain_exactly_the_same_server_message(self):
        preview = self.post("cart_review")
        ready = self.post("cart_whatsapp", accepted="yes")
        message = whatsapp_message(calculate_cart([self.item()]))
        self.assertEqual(preview.context["message"], message)
        self.assertEqual(ready.context["message"], message)
        self.assertEqual(parse_qs(urlparse(ready.context["ready_url"]).query)["text"], [message])

    def test_review_has_warning_and_cancel_without_ready_link(self):
        response = self.post("cart_review")
        self.assertContains(response, PRICE_WARNING)
        self.assertContains(response, "Volver al carrito")
        self.assertContains(response, "Continuar a WhatsApp")
        self.assertNotContains(response, 'id="whatsapp-ready"')
        self.assertNotContains(self.post("cart_whatsapp"), 'id="whatsapp-ready"')
        self.assertContains(response, 'id="review-title" class="visually-hidden" tabindex="-1"')
        self.assertNotContains(response, "El texto se incluye completo.")
        self.assertContains(response, "Copiar mensaje completo")

    def test_acceptance_generates_link_only_after_revalidation(self):
        response = self.post("cart_whatsapp", accepted="yes")
        self.assertContains(response, 'id="whatsapp-ready"')
        self.assertContains(response, 'target="_blank" rel="noopener noreferrer"')
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
