from django.test import TestCase
from django.urls import reverse

from .models import Category, Product
from .templatetags.catalog_format import ars


class CatalogViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Repostería", slug="reposteria")
        self.product = Product.objects.create(
            category=self.category, name="Chocolate de test", brand="Marca de test",
            retail_price="1234", wholesale_price="1000", wholesale_condition="Consultar condiciones",
        )

    def test_active_catalog_and_integer_price(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, self.product.name)
        self.assertContains(response, "$ 1.234")
        self.assertNotContains(response, "Consultar condiciones")
        self.assertNotContains(response, "Minorista")
        self.assertNotContains(response, "Mayorista")
        self.assertNotContains(response, "$ 1.000")
        self.assertContains(response, "/ kg")

    def test_catalog_link_is_contextual_and_old_cart_notice_is_removed(self):
        for url, count in (("/", 0), ("/?q=Chocolate", 0), ("/carrito/", 1)):
            response = self.client.get(url)
            self.assertContains(response, '>Catálogo</a>', count=count)
            self.assertNotContains(response, "Ver horarios")
            self.assertNotContains(response, "El carrito se guarda sólo en este navegador. No confirma un pedido.")

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

    def test_search_ranks_name_brand_and_description_with_filters(self):
        by_description = Product.objects.create(category=self.category, name="A", description="CaCaO", retail_price=1)
        by_brand = Product.objects.create(category=self.category, name="B", brand="CACAO", description="cacao", retail_price=1)
        by_name = Product.objects.create(category=self.category, name="Cacao Z", brand="cacao", retail_price=1)
        Product.objects.create(category=self.category, name="Cacao oculto", is_active=False, retail_price=1)
        other = Category.objects.create(name="Otra", slug="otra")
        Product.objects.create(category=other, name="Cacao otra categoría", retail_price=1)
        response = self.client.get("/", {"q": "cAcAo", "categoria": self.category.slug})
        self.assertEqual(list(response.context["page"]), [by_name, by_brand, by_description])
        self.assertContains(response, 'name="q" value="cAcAo"')
        self.assertContains(response, 'value="reposteria" selected')
        self.assertContains(response, "Todas las categorías")
        self.assertNotContains(response, "Sujeto a confirmación comercial.")
        self.assertNotContains(response, "d+s")

    def test_pagination_preserves_filters(self):
        Product.objects.bulk_create([
            Product(category=self.category, name=f"Chocolate {i:02}", retail_price=1)
            for i in range(25)
        ])
        response = self.client.get("/", {"q": "Chocolate", "categoria": self.category.slug})
        self.assertEqual(len(response.context["page"]), 20)
        self.assertContains(response, "page=2&amp;q=Chocolate&amp;categoria=reposteria")

    def test_product_content_is_escaped(self):
        self.product.name = '<script>alert("test")</script>'
        self.product.save()
        response = self.client.get("/")
        self.assertNotContains(response, "<script>alert")
        self.assertContains(response, "&lt;script&gt;")

    def test_currency_format(self):
        self.assertEqual(ars("0.99"), "$ 0")
        self.assertEqual(ars("1000000.99"), "$ 1.000.000")

    def test_image_enlargement_only_for_existing_photo(self):
        response = self.client.get("/")
        self.assertNotContains(response, 'class="product-image-open"')
        self.assertContains(response, 'id="product-image-dialog"', count=1)
        self.product.image = "products/test.webp"
        self.product.save()
        response = self.client.get("/")
        self.assertContains(response, 'class="product-image-open"', count=1)
        self.assertContains(response, f'aria-label="Ver imagen ampliada de {self.product.name}"')
        self.assertContains(response, 'loading="lazy" decoding="async"')
        self.assertContains(response, 'aria-label="Cerrar imagen"')
        self.assertContains(response, 'aria-describedby="image-dialog-description"')
        self.assertNotContains(response, 'id="image-dialog-title"')
        self.assertNotContains(response, 'class="image-dialog-heading"')

    def test_brand_navigation_and_requested_texts(self):
        response = self.client.get("/")
        self.assertContains(response, '/static/img/logo.webp')
        self.assertContains(response, 'href="https://www.instagram.com/_dulceysalado1/"')
        self.assertNotContains(response, "Todo para tus ideas")
        self.assertNotContains(self.client.get(reverse("cart")), "Tu selección")
        self.assertContains(response, '<h1 id="catalog-title" class="visually-hidden">Nuestros productos</h1>')
        self.assertContains(response, 'placeholder="Buscar productos, marcas y más..."')
        self.assertContains(response, 'class="visually-hidden" for="category-filter"')
        self.assertContains(response, 'class="visually-hidden" for="catalog-search"')
        for text in ("Encontrá lo que necesitás.", "Consultá nuestros productos y precios.", "Buscar por nombre, marca o descripción", "Precios en pesos argentinos (ARS)."):
            self.assertNotContains(response, text)
        self.assertNotContains(self.client.get(reverse("cart")), "Cantidades y precios estimados.")
        self.assertNotContains(response, "Repostería · Dietética · Cotillón")
        self.assertNotContains(response, "Mi cuenta")

    def test_header_navigation_marks_only_current_page(self):
        for name in ("home", "cart"):
            response = self.client.get(reverse(name))
            self.assertContains(response, 'aria-label="Navegación principal"')
            if name == "home":
                self.assertNotContains(response, f'href="{reverse(name)}" aria-current="page"')
            else:
                self.assertContains(response, f'href="{reverse(name)}" aria-current="page"', count=1)

    def test_header_search_and_categories_are_available_from_cart(self):
        Category.objects.create(name="Privada", slug="privada", is_active=False)
        for name in ("home", "cart"):
            response = self.client.get(reverse(name))
            self.assertContains(response, 'action="/" method="get" class="search-form" role="search"', count=1)
            self.assertContains(response, 'id="catalog-search"', count=1)
            self.assertContains(response, 'id="category-filter"', count=1)
            self.assertContains(response, 'href="/?categoria=reposteria&amp;q="')
            self.assertNotContains(response, "privada")
            html = response.content.decode()
            self.assertLess(html.index('id="catalog-search"'), html.index('</header>'))
            self.assertLess(html.index('id="category-filter"'), html.index('</header>'))

    def test_cart_frame_is_same_origin_and_reuses_the_cart(self):
        response = self.client.get(reverse("cart"), {"panel": "1"})
        self.assertTemplateUsed(response, "cart_frame.html")
        self.assertTemplateUsed(response, "includes/cart_app.html")
        self.assertEqual(response.headers["X-Frame-Options"], "SAMEORIGIN")
        self.assertContains(response, 'class="cart-frame"')
        self.assertContains(response, 'id="cart-app" data-panel="1"')
        self.assertNotContains(response, '<header')
        self.assertNotContains(response, 'id="cart-drawer"')
        response = self.client.get(reverse("cart"))
        self.assertTemplateUsed(response, "cart.html")
        self.assertContains(response, 'id="cart-app" data-panel="0"')
        self.assertContains(response, '<header')

    def test_loading_status_never_reserves_visual_space(self):
        for query in ({}, {"panel": "1"}):
            response = self.client.get(reverse("cart"), query)
            self.assertContains(response, '<p id="cart-loading" class="visually-hidden" role="status"></p>')
            self.assertNotContains(response, 'role="status">Consultando el catálogo vigente')

    def test_drawer_only_shows_a_fallback_on_load_error(self):
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, "Cargando carrito")
        self.assertContains(response, 'class="cart-drawer-loading" role="alert" hidden')
        self.assertContains(response, "No se pudo cargar el carrito.")

    def test_catalog_keeps_cart_link_and_lazy_drawer(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, 'id="cart-drawer"', count=1)
        self.assertContains(response, 'src="about:blank"')
        self.assertContains(response, 'data-frame-url="/carrito/?panel=1"')
        self.assertContains(response, 'title="Productos y total del carrito"')

    def test_empty_frame_offers_add_products_instead_of_whatsapp(self):
        response = self.client.post(reverse("cart_refresh"), {"items": "[]", "panel": "1"})
        self.assertContains(response, 'data-close-cart>Agregar productos</button>')
        self.assertNotContains(response, "Revisar y preparar WhatsApp")
        self.assertContains(self.client.post(reverse("cart_refresh"), {"items": "[]"}), 'href="/">Agregar productos</a>')

    def test_45_products_have_three_stable_filtered_pages_and_ranges(self):
        Product.objects.bulk_create([
            Product(category=self.category, name=f"Chocolate {i // 2:02}", retail_price=1)
            for i in range(44)
        ])
        other = Category.objects.create(name="Otra", slug="otra")
        Product.objects.create(category=other, name="Chocolate excluido", retail_price=1)
        seen = []
        for number, start, end in ((1, 1, 20), (2, 21, 40), (3, 41, 45)):
            response = self.client.get("/", {"q": "Chocolate", "categoria": self.category.slug, "page": number})
            self.assertContains(response, f"{start}–{end} de 45 productos")
            self.assertContains(response, f"Página {number} de 3")
            self.assertNotContains(response, "Chocolate excluido")
            seen.extend(product.pk for product in response.context["page"])
            if number < 3:
                self.assertContains(response, f"page={number + 1}&amp;q=Chocolate&amp;categoria=reposteria")
        self.assertEqual(len(seen), len(set(seen)))
        self.assertEqual(seen, list(Product.objects.filter(category=self.category).values_list("pk", flat=True)))
        for invalid, expected in (("inexistente", 1), ("999", 3), ("0", 3), ("-1", 3)):
            response = self.client.get("/", {"q": "Chocolate", "categoria": self.category.slug, "page": invalid})
            self.assertEqual(response.context["page"].number, expected)

    def test_empty_and_single_page_have_no_pagination(self):
        response = self.client.get("/", {"q": "no existe"})
        self.assertContains(response, "0 de 0 productos")
        self.assertNotContains(response, 'class="pagination"')
        response = self.client.get("/")
        self.assertContains(response, "1–1 de 1 producto")
        self.assertNotContains(response, 'class="pagination"')
