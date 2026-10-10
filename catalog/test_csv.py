import csv
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


class ProductCSVTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Repostería", slug="reposteria")
        self.other = Category.objects.create(name="Cotillón", slug="cotillon")
        self.product = Product.objects.create(
            category=self.category, name="Chocolate", brand='Marca; "Especial"', description="Línea 1\nLínea 2",
            sale_unit="kg", quantity_step="0.10", retail_price="1234.56", wholesale_price="1000.01",
            wholesale_condition="Consultar", is_active=False,
        )
        Product.objects.create(category=self.other, name="Velas", retail_price="20")
        self.staff = get_user_model().objects.create_user(username="csv-staff", is_staff=True)
        self.url = reverse("admin:catalog_product_export_csv")

    def allow(self, permission="view_product"):
        self.staff.user_permissions.add(Permission.objects.get(codename=permission))
        self.client.force_login(self.staff)

    def rows(self, response):
        return list(csv.reader(StringIO(response.content.decode("utf-8-sig")), delimiter=";"))

    def test_permissions_and_get_only(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.allow()
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.post(self.url).status_code, 405)
        self.staff.user_permissions.clear()
        self.allow("change_product")
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.staff.is_staff = False
        self.staff.save()
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_encoding_exact_columns_and_excel_decimal_format(self):
        self.allow()
        response = self.client.get(self.url)
        self.assertTrue(response.content.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        rows = self.rows(response)
        self.assertEqual(rows[0], ["Categoría", "Nombre", "Marca", "Descripción", "Unidad de venta", "Incremento de cantidad", "Precio minorista", "Precio mayorista", "Condición mayorista", "Activo"])
        self.assertEqual(rows[1], ["Repostería", "Chocolate", 'Marca; "Especial"', "Línea 1\nLínea 2", "kg", "0,10", "1234,56", "1000,01", "Consultar", "No"])
        self.assertEqual(rows[2][7], "")
        self.assertEqual(rows[2][-1], "Sí")

    def test_filters_search_and_all_pages_match_admin_queryset(self):
        self.allow()
        Product.objects.bulk_create([
            Product(category=self.category, name=f"Chocolate {i:03}", sale_unit="kg", quantity_step="0.1", retail_price="1", is_active=False)
            for i in range(110)
        ])
        filters = {"category__id__exact": self.category.pk, "sale_unit__exact": "kg", "is_active__exact": "0", "q": "chocolate", "p": "1"}
        response = self.client.get(reverse("admin:catalog_product_changelist"), filters)
        self.assertEqual(response.status_code, 200)
        self.assertLess(len(response.context["cl"].result_list), 111)
        self.assertContains(response, "Exportar CSV")
        self.assertNotContains(response, 'class="addlink"')
        exported = self.rows(self.client.get(self.url, filters))[1:]
        self.assertEqual(len(exported), 111)
        self.assertEqual({row[1] for row in exported}, set(response.context["cl"].queryset.values_list("name", flat=True)))
        self.assertEqual(len(self.rows(self.client.get(self.url))), 113)
        self.assertEqual(len(self.rows(self.client.get(self.url, {"is_active__exact": "1"}))), 2)
        self.assertEqual(self.client.get(self.url, {"invalid_field": "x"}).status_code, 400)

    def test_formula_injection_is_prefixed_in_all_text_columns(self):
        self.allow()
        self.category.name = "=SUM(1;1)"
        self.category.save()
        for prefix in ("=", "+", "-", "@", "  =", "\t", "\r", "\n", "\ufeff="):
            self.product.name = prefix + "Text"
            self.product.brand = self.product.description = self.product.wholesale_condition = self.product.name
            self.product.save()
            row = self.rows(self.client.get(self.url, {"category__id__exact": self.category.pk}))[1]
            for index in (0, 1, 2, 3, 8):
                self.assertTrue(row[index].startswith("'"), (prefix, index, row))
