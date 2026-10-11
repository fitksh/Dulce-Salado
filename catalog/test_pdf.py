import csv
import re
import shutil
import subprocess
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import skipUnless
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.html import escape
from PIL import Image

from .models import Category, Product

POPPLER = all(shutil.which(tool) for tool in ("pdfinfo", "pdftotext", "pdfimages"))


class PDFTestCase(TestCase):
    def setUp(self):
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        media_settings = override_settings(MEDIA_ROOT=self.media.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)
        self.category = Category.objects.create(name="Repostería & dietética", slug="reposteria")
        self.product = Product.objects.create(
            category=self.category, name="[DEMO] Chocolate ñ <especial>", brand="Café Águila",
            description="Línea uno\nLínea dos & más", sale_unit="kg", retail_price="1234.56",
            wholesale_price="1000.01", wholesale_condition="Desde 3 kg; confirmar con el comercio", is_active=False,
        )
        self.staff = get_user_model().objects.create_user(username="pdf-staff", is_staff=True)
        self.urls = [reverse(f"admin:catalog_product_export_pdf_{variant}") for variant in ("images", "plain")]

    def allow(self, permission="view_product"):
        self.staff.user_permissions.add(Permission.objects.get(codename=permission))
        self.client.force_login(self.staff)

    def pdf(self, url=None, filters=None):
        response = self.client.get(url or self.urls[0], filters or {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment; filename=", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF-"))
        self.assertTrue(response.content.rstrip().endswith(b"%%EOF"))
        return response.content

    def tool(self, tool, data, *arguments):
        return subprocess.run([tool, *arguments], input=data, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, check=True).stdout.decode("utf-8")

    def text(self, data):
        return self.tool("pdftotext", data, "-", "-")

    def image_count(self, data):
        return len(re.findall(r"^\s+\d+\s+\d+\s+image\s", self.tool("pdfimages", data, "-list", "-"), re.MULTILINE))


class ProductPDFTests(PDFTestCase):
    def test_both_variants_permissions_headers_and_get_only(self):
        for url in self.urls:
            with self.subTest(url=url):
                self.client.logout()
                self.assertEqual(self.client.get(url).status_code, 302)
                self.client.force_login(self.staff)
                self.assertEqual(self.client.get(url).status_code, 403)
                for permission in ("view_product", "change_product"):
                    self.allow(permission)
                    self.pdf(url)
                    self.assertEqual(self.client.post(url).status_code, 405)
                    self.assertEqual(self.client.put(url).status_code, 405)
                    self.staff.user_permissions.clear()
                self.staff.is_staff = False
                self.staff.save()
                self.assertEqual(self.client.get(url).status_code, 302)
                self.staff.is_staff = True
                self.staff.save()

    def test_admin_buttons_preserve_all_filters_and_invalid_filters_fail(self):
        self.allow()
        filters = {"category__id__exact": self.category.pk, "sale_unit__exact": "kg",
                   "is_active__exact": "0", "q": "Chocolate", "o": "-1", "p": "0"}
        response = self.client.get(reverse("admin:catalog_product_changelist"), filters)
        self.assertContains(response, "Exportar CSV")
        for url, label in zip(self.urls, ("PDF con imágenes", "PDF sin imágenes")):
            self.assertContains(response, label)
            self.assertContains(response, f'href="{url}?{escape(urlencode(filters))}"')
            self.assertEqual(self.client.get(url, {"invalid_field": "x"}).status_code, 400)

    @skipUnless(POPPLER, "Instalar poppler-utils para inspeccionar contenido/paginación PDF")
    def test_a4_unicode_prices_optional_fields_and_inactive_demo_are_readable(self):
        self.allow()
        for url in self.urls:
            data = self.pdf(url)
            text = " ".join(self.text(data).split())
            for value in ("Dulce y Salado", "Catálogo de productos", "Página 1", self.product.name,
                          self.category.name, self.product.brand, "Línea uno Línea dos & más",
                          "Unidad de venta: kg", "Precio minorista: $ 1.234,56", "Precio mayorista: $ 1.000,01",
                          self.product.wholesale_condition, "Estado: Inactivo", "Precios estimativos en ARS"):
                self.assertIn(value, text)
            for forbidden in ("ID:", "Creado:", "Actualizado:", "Incremento", "Stock", "products/"):
                self.assertNotIn(forbidden, text)
            self.assertRegex(self.tool("pdfinfo", data, "-"), r"Page size:\s+595\.[\d]+ x 841\.[\d]+ pts \(A4\)")
        self.product.brand = self.product.description = self.product.wholesale_condition = ""
        self.product.wholesale_price = None
        self.product.is_active = True
        self.product.save()
        text = self.text(self.pdf(self.urls[1]))
        for omitted in ("Marca:", "Precio mayorista:", "Condición mayorista:", "Estado:", "Sin imagen"):
            self.assertNotIn(omitted, text)

    @skipUnless(POPPLER, "Instalar poppler-utils para inspeccionar contenido/paginación PDF")
    def test_filters_order_and_all_pages_match_csv_and_changelist(self):
        self.allow()
        Product.objects.bulk_create([
            Product(category=self.category, name=f"Chocolate QA {i:03}", brand="Buscar marca", sale_unit="kg",
                    retail_price="1", is_active=False) for i in range(110)
        ])
        other = Category.objects.create(name="Otra", slug="otra")
        Product.objects.create(category=other, name="Chocolate excluido", retail_price="2")
        filters = {"category__id__exact": self.category.pk, "sale_unit__exact": "kg", "is_active__exact": "0",
                   "q": "Chocolate", "o": "-1", "p": "1"}
        change_list = self.client.get(reverse("admin:catalog_product_changelist"), filters).context["cl"]
        self.assertLess(len(change_list.result_list), 111)
        csv_response = self.client.get(reverse("admin:catalog_product_export_csv"), filters)
        rows = list(csv.reader(StringIO(csv_response.content.decode("utf-8-sig")), delimiter=";"))[1:]
        names = [row[1] for row in rows]
        self.assertEqual(names, list(change_list.queryset.values_list("name", flat=True)))
        self.assertEqual(len(names), 111)
        for url in self.urls:
            text = " ".join(self.text(self.pdf(url, filters)).split())
            positions = [text.index(name) for name in names]
            self.assertEqual(positions, sorted(positions))
            self.assertNotIn("Chocolate excluido", text)
            self.assertIn("Chocolate excluido", self.text(self.pdf(url)))
            self.assertNotIn("Chocolate QA", self.text(self.pdf(url, {"is_active__exact": "1"})))
            self.assertIn("Chocolate QA", self.text(self.pdf(url, {"q": "Buscar marca"})))

    @skipUnless(POPPLER, "Instalar poppler-utils para inspeccionar contenido/paginación PDF")
    def test_empty_pdf_is_valid_and_explains_filters(self):
        self.allow()
        for url in self.urls:
            self.assertIn("No hay productos para los filtros seleccionados", self.text(self.pdf(url, {"q": "inexistente"})))

    @skipUnless(POPPLER, "Instalar poppler-utils para inspeccionar contenido/paginación PDF")
    def test_photos_keep_proportions_are_reduced_and_stored_files_do_not_change(self):
        self.allow()
        sources = []
        directory = Path(self.media.name) / "products"
        directory.mkdir()
        for index, size in enumerate(((1200, 400), (400, 1200), (600, 600))):
            path = directory / f"qa-{index}.webp"
            Image.new("RGB", size, "orange").save(path, "WEBP")
            sources.append((path, path.read_bytes()))
            Product.objects.create(category=self.category, name=f"Foto QA {index}", retail_price="1", image=f"products/{path.name}")
        data = self.pdf()
        self.assertEqual(self.image_count(data), 3)
        listing = self.tool("pdfimages", data, "-list", "-")
        for width, height in ((240, 80), (80, 240), (240, 240)):
            self.assertRegex(listing, rf"image\s+{width}\s+{height}\s")
        self.assertEqual(self.image_count(self.pdf(self.urls[1])), 0)
        for path, before in sources:
            self.assertEqual(path.read_bytes(), before)
        self.assertLess(len(data), 100_000)

    @skipUnless(POPPLER, "Instalar poppler-utils para inspeccionar contenido/paginación PDF")
    def test_missing_corrupt_or_absent_photos_do_not_abort_export(self):
        self.allow()
        path = Path(self.media.name) / "invalid.webp"
        path.write_bytes(b"not an image")
        Product.objects.create(category=self.category, name="Foto corrupta", retail_price="1", image=path.name)
        Product.objects.create(category=self.category, name="Foto faltante", retail_price="1", image="missing.webp")
        text = " ".join(self.text(self.pdf()).split())
        self.assertEqual(text.count("Foto no disponible"), 2)
        self.assertIn("Sin imagen", text)
        self.assertIn("Foto corrupta", text)
        self.assertIn("Foto faltante", text)
        self.assertEqual(self.image_count(self.pdf()), 0)
        plain = self.text(self.pdf(self.urls[1]))
        self.assertNotIn("Foto no disponible", plain)
        self.assertNotIn("Sin imagen", plain)

    @skipUnless(POPPLER, "Instalar poppler-utils para inspeccionar contenido/paginación PDF")
    def test_oversized_description_splits_across_pages_without_truncation(self):
        self.allow()
        self.product.name = "Ñ" * 180
        self.product.description = "Descripción larga con acentos, ñ y <texto>. " * 300 + "FIN DESCRIPCIÓN LARGA"
        self.product.save()
        for url in self.urls:
            data = self.pdf(url)
            text = self.text(data)
            pages = [page for page in text.split("\f") if page.strip()]
            self.assertGreater(len(pages), 2)
            body_lines = [line for page in pages for line in page.splitlines()
                          if line not in ("Dulce y Salado", "Catálogo de productos")
                          and not line.startswith(("Precios estimativos en ARS", "Página "))]
            normalized = " ".join(" ".join(body_lines).split())
            self.assertIn("FIN DESCRIPCIÓN LARGA", normalized)
            self.assertEqual(normalized.count("Descripción larga con acentos, ñ y <texto>."), 300)
            self.assertIn(self.product.name, "".join(text.split()))
            self.assertIn("Estado: Inactivo", text)
            for number, page in enumerate(pages, 1):
                self.assertIn("Dulce y Salado", page)
                self.assertIn(f"Página {number}", page)
                self.assertIn("Precios estimativos en ARS", page)

    @skipUnless(POPPLER, "Instalar poppler-utils para inspeccionar contenido/paginación PDF")
    def test_normal_products_stay_together_at_page_breaks(self):
        self.allow()
        Product.objects.bulk_create([
            Product(category=self.category, name=f"Registro QA {i:02}", brand=f"Marca QA {i:02}", retail_price="15.25",
                    wholesale_condition=f"Condición QA {i:02}") for i in range(15)
        ])
        for url in self.urls:
            pages = self.text(self.pdf(url)).split("\f")
            for index in range(15):
                page = next(page for page in pages if f"Registro QA {index:02}" in page)
                self.assertIn(f"Marca QA {index:02}", page)
                self.assertIn(f"Condición QA {index:02}", page)
                self.assertIn("Precio minorista: $ 15,25", page)


class ProductTablePDFTests(PDFTestCase):
    def setUp(self):
        super().setUp()
        self.urls = [reverse(f"admin:catalog_product_export_pdf_table_{variant}") for variant in ("images", "plain")]

    def test_permissions_methods_buttons_and_invalid_filters(self):
        ProductPDFTests.test_both_variants_permissions_headers_and_get_only(self)
        self.allow()
        filters = {"category__id__exact": self.category.pk, "q": "Chocolate", "o": "-1", "p": "0"}
        response = self.client.get(reverse("admin:catalog_product_changelist"), filters)
        self.assertContains(response, "PDF tabla compacta")
        self.assertContains(response, "PDF tabla con imágenes")
        for url in self.urls:
            self.assertContains(response, f'href="{url}?{escape(urlencode(filters))}"')
            self.assertEqual(self.client.get(url, {"invalid_field": "x"}).status_code, 400)

    @skipUnless(POPPLER, "Instalar poppler-utils para inspeccionar tablas PDF")
    def test_landscape_text_prices_optional_inactive_and_no_category_or_images(self):
        self.allow()
        for url in self.urls:
            data = self.pdf(url)
            text = " ".join(self.text(data).split())
            for value in (self.product.name, self.product.brand, "Línea uno Línea dos & más",
                          "$ 1.234,56", "$ 1.000,01", self.product.wholesale_condition, "Estado: Inactivo"):
                self.assertIn(value, text)
            self.assertNotIn(self.category.name, text)
            self.assertNotIn("Categoría", text)
            self.assertEqual(self.image_count(data), 0)
            self.assertRegex(self.tool("pdfinfo", data, "-"), r"Page size:\s+841\.[\d]+ x 595\.[\d]+ pts \(A4\)")
            self.assertIn("tabla-", self.client.get(url)["Content-Disposition"])
        self.product.brand = self.product.description = self.product.wholesale_condition = ""
        self.product.wholesale_price = None
        self.product.is_active = True
        self.product.save()
        text = self.text(self.pdf(self.urls[1]))
        for omitted in ("None", "null", "Estado:", "Sin imagen"):
            self.assertNotIn(omitted, text)

    @skipUnless(POPPLER, "Instalar poppler-utils para inspeccionar tablas PDF")
    def test_filters_order_all_pages_and_empty(self):
        ProductPDFTests.test_filters_order_and_all_pages_match_csv_and_changelist(self)
        ProductPDFTests.test_empty_pdf_is_valid_and_explains_filters(self)

    @skipUnless(POPPLER, "Instalar poppler-utils para inspeccionar tablas PDF")
    def test_repeated_headers_normal_rows_stay_together_and_long_text_is_complete(self):
        self.allow()
        Product.objects.bulk_create([
            Product(category=self.category, name=f"Registro QA {i:02}", brand=f"Marca QA {i:02}", retail_price="15.25",
                    description=f"Descripción QA {i:02}. " * 4, wholesale_condition=f"Condición QA {i:02}")
            for i in range(25)
        ])
        for url in self.urls:
            pages = [page for page in self.text(self.pdf(url)).split("\f") if page.strip()]
            self.assertGreater(len(pages), 1)
            for number, page in enumerate(pages, 1):
                prices = ("Precio minorista", "Precio mayorista") if url == self.urls[0] else ("$ Min.", "$ May.")
                for heading in ("Dulce y Salado", "Producto", "Marca", "Descripción", "Unidad", *prices,
                                "Precios estimativos en ARS", f"Página {number}"):
                    self.assertIn(heading, " ".join(page.split()))
            for index in range(25):
                page = next(page for page in pages if f"Registro QA {index:02}" in page)
                self.assertIn(f"Marca QA {index:02}", page)
                self.assertIn(f"Condición QA {index:02}", page)
        self.product.name = "Ñ" * 180
        self.product.description = "Descripción larga con acentos y ñ. " * 300 + "FIN DESCRIPCIÓN LARGA"
        self.product.wholesale_condition = "Condición extensa " * 15 + "FIN CONDICIÓN"
        self.product.save()
        for url in self.urls:
            data = self.pdf(url, {"q": self.product.name})
            text = self.text(data)
            self.assertGreater(text.count("\f"), 2)
            self.assertIn("FIN DESCRIPCIÓN LARGA", " ".join(text.split()))
            self.assertIn("FIN CONDICIÓN", " ".join(text.split()))
            # La extracción intercala otras columnas entre fragmentos de página.
            # Ambas palabras únicas comprueban las 300 repeticiones completas.
            self.assertEqual(len(re.findall(r"\bacentos\b", text)), 300)
            self.assertEqual(text.count("ñ."), 300)
            self.assertIn(self.product.name, "".join(text.split()))
            for page in text.split("\f"):
                if page.strip():
                    self.assertIn("Producto", page)
                    self.assertIn("Descripción", page)
                    self.assertIn("Dulce y Salado", page)
                    self.assertIn("Precios estimativos en ARS", page)

    @skipUnless(POPPLER, "Instalar poppler-utils para inspeccionar tablas PDF")
    def test_table_photos_reuse_contain_missing_and_corrupt_handling(self):
        self.allow()
        ProductPDFTests.test_photos_keep_proportions_are_reduced_and_stored_files_do_not_change(self)
        text = " ".join(self.text(self.pdf()).split())
        for heading in ("Imagen", "Producto", "Marca", "Descripción", "Unidad de venta", "Precio minorista",
                        "Precio mayorista", "Condición mayorista"):
            self.assertIn(heading, text)

    @skipUnless(POPPLER, "Instalar poppler-utils para inspeccionar tablas PDF")
    def test_table_missing_and_corrupt_photos_keep_the_record(self):
        ProductPDFTests.test_missing_corrupt_or_absent_photos_do_not_abort_export(self)
