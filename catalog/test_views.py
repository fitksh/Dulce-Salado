from django.test import TestCase
from django.urls import reverse

from .models import Category, Product
from .templatetags.catalog_format import ars


class CatalogViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Repostería", slug="reposteria")
        self.product = Product.objects.create(
            category=self.category, name="Chocolate de test", brand="Marca de test",
            retail_price="1234.56", wholesale_price="1000", wholesale_condition="Consultar condiciones",
        )

    def test_active_catalog_and_decimal_price(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, self.product.name)
        self.assertContains(response, "$ 1.234,56")
        self.assertContains(response, "Consultar condiciones")
        self.assertContains(response, "/ unidad")

    def test_inactive_product_and_category_are_hidden(self):
        hidden = Category.objects.create(name="Oculta", slug="oculta", is_active=False)
        Product.objects.create(category=hidden, name="Producto oculto", retail_price=1)
        self.product.is_active = False
        self.product.save()
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, "Producto oculto")
        self.assertNotContains(response, "Oculta")
        self.assertNotContains(response, self.product.name)
        self.assertEqual(self.client.get("/?categoria=oculta").status_code, 404)

    def test_search_by_name_or_brand_and_category(self):
        for query in ("CHOCOLATE", "marca DE"):
            response = self.client.get(reverse("home"), {"q": query, "categoria": self.category.slug})
            self.assertContains(response, self.product.name)
        other = Category.objects.create(name="Otra", slug="otra")
        self.assertNotContains(self.client.get("/", {"categoria": other.slug}), self.product.name)

    def test_empty_state_and_optional_wholesale(self):
        self.assertContains(self.client.get("/?q=inexistente"), "No encontramos productos")
        self.product.wholesale_price = None
        self.product.save()
        self.assertNotContains(self.client.get("/"), "Mayorista")
        Product.objects.all().delete()
        self.assertContains(self.client.get("/"), "Estamos preparando nuestro catálogo")

    def test_pagination_preserves_filters(self):
        Product.objects.bulk_create([
            Product(category=self.category, name=f"Chocolate {i:02}", retail_price=1)
            for i in range(25)
        ])
        response = self.client.get("/", {"q": "Chocolate", "categoria": self.category.slug})
        self.assertEqual(len(response.context["page"]), 24)
        self.assertContains(response, "page=2&amp;q=Chocolate&amp;categoria=reposteria")

    def test_product_content_is_escaped(self):
        self.product.name = '<script>alert("test")</script>'
        self.product.save()
        response = self.client.get("/")
        self.assertNotContains(response, "<script>alert")
        self.assertContains(response, "&lt;script&gt;")

    def test_currency_format(self):
        self.assertEqual(ars("0.10"), "$ 0,10")
        self.assertEqual(ars("1000000.05"), "$ 1.000.000,05")

    def test_brand_navigation_and_requested_texts(self):
        response = self.client.get("/")
        self.assertContains(response, '/static/img/logo.webp')
        self.assertContains(response, 'href="https://www.instagram.com/_dulceysalado1/"')
        self.assertNotContains(response, "Todo para tus ideas")
        self.assertNotContains(self.client.get(reverse("cart")), "Tu selección")
