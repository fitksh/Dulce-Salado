import csv
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase

from .csv_import import (
    HEADERS,
    MAX_FILE_BYTES,
    MAX_ROWS,
    PreviewChanged,
    create_from_preview,
    preview_rows,
    read_csv,
)
from .models import Category, Product


def csv_upload(rows, *, delimiter=";", bom=True, name="productos.csv"):
    stream = StringIO(newline="")
    writer = csv.writer(stream, delimiter=delimiter)
    writer.writerow(HEADERS)
    writer.writerows(rows)
    return SimpleUploadedFile(name, stream.getvalue().encode("utf-8-sig" if bom else "utf-8"), content_type="text/csv")


def csv_row(**changes):
    values = ["Repostería", "Producto ficticio QA", "", "", "kg", "", "14500,00", "", "", ""]
    for key, value in changes.items():
        values[int(key.removeprefix("column"))] = value
    return values


class CSVImportEngineTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Repostería", slug="reposteria")

    def preview(self, rows, **options):
        return preview_rows(read_csv(csv_upload(rows, **options)))

    def test_encoding_separators_quotes_multiline_and_physical_row_numbers(self):
        for bom in (True, False):
            for separator in (";", ","):
                with self.subTest(bom=bom, separator=separator):
                    preview = self.preview([csv_row(column1='QA; "Especial", ñ', column2="Café Águila",
                                                    column3="Línea uno; con coma,\nLínea dos"), csv_row(column1="Segundo QA")],
                                           bom=bom, delimiter=separator)
                    self.assertEqual(preview.error_count, 0)
                    self.assertEqual([row.number for row in preview.rows], [2, 4])
                    self.assertEqual(preview.rows[0].product.description, "Línea uno; con coma,\nLínea dos")
                    self.assertEqual(Product.objects.count(), 0)

    def test_optional_texts_nullable_wholesale_defaults_and_inactive(self):
        for unit, step in (("kg", "0.10"), ("unidad", "1.00"), ("paquete", "1.00")):
            for active, expected in (("", True), ("Sí", True), ("No", False), ("true", True), ("FALSE", False), ("1", True), ("0", False)):
                with self.subTest(unit=unit, active=active):
                    product = self.preview([csv_row(column4=unit, column9=active)]).rows[0].product
                    self.assertEqual(product.quantity_step, Decimal(step))
                    self.assertIsInstance(product.retail_price, Decimal)
                    self.assertEqual(product.retail_price, Decimal("14500.00"))
                    self.assertIsNone(product.wholesale_price)
                    self.assertEqual((product.brand, product.description, product.wholesale_condition), ("", "", ""))
                    self.assertEqual(product.is_active, expected)

    def test_decimal_prices_zero_and_wholesale_above_retail_are_allowed(self):
        for value, expected in (("14500,00", "14500.00"), ("14500.00", "14500.00"), ("14500", "14500"), ("0", "0")):
            product = self.preview([csv_row(column6=value, column7="18000,00")]).rows[0].product
            self.assertEqual(product.retail_price, Decimal(expected))
            self.assertEqual(product.wholesale_price, Decimal("18000.00"))

    def test_explicit_steps_include_fifty_grams_and_whole_units(self):
        for unit, step in (("kg", "0.05"), ("kg", "0,10"), ("kg", "1.00"), ("unidad", "1.00"), ("paquete", "2")):
            preview = self.preview([csv_row(column4=unit, column5=step)])
            self.assertEqual(preview.error_count, 0)
            self.assertEqual(preview.rows[0].product.quantity_step, Decimal(step.replace(",", ".")))

    def test_required_fields_unknown_categories_units_active_and_model_limits(self):
        for index, value in ((0, ""), (0, "Inexistente"), (1, " "), (4, ""), (4, "litro"), (6, ""),
                             (9, "quizás"), (1, "x" * 181), (2, "x" * 101), (8, "x" * 301), (3, "x" * 4001)):
            with self.subTest(index=index):
                row = csv_row()
                row[index] = value
                preview = self.preview([row])
                self.assertEqual(preview.error_count, 1)
                self.assertTrue(preview.rows[0].errors)
                self.assertEqual(preview.rows[0].number, 2)
                with self.assertRaises(ValidationError):
                    create_from_preview(read_csv(csv_upload([row])), preview.fingerprint)
                self.assertEqual(Product.objects.count(), 0)

    def test_ambiguous_numbers_negative_nonfinite_expressions_and_invalid_steps(self):
        for index in (5, 6, 7):
            for value in ("-1", "=2+3", "1e3", "NaN", "Infinity", "1.234,56", "1,234.56", "1.234", "1,234", "$ 100", "1 000", "0.001"):
                with self.subTest(index=index, value=value):
                    row = csv_row()
                    row[index] = value
                    self.assertEqual(self.preview([row]).error_count, 1)
        for unit, step in (("kg", "0"), ("unidad", "0.05"), ("paquete", "0,10"), ("kg", "10000000")):
            self.assertEqual(self.preview([csv_row(column4=unit, column5=step)]).error_count, 1)
        self.assertEqual(self.preview([csv_row(column6="10000000000")]).error_count, 1)

    def test_normalized_existing_real_demo_and_file_duplicates_are_omitted(self):
        real = Product.objects.create(category=self.category, name="Chocolate Águila", brand="Café", retail_price="99")
        demo = Product.objects.create(category=self.category, name="[DEMO] Prueba", retail_price="5", is_active=False)
        before = list(Product.objects.values())
        rows = [csv_row(column0=" REPOSTERIA ", column1="chocolate   aguila", column2="CAFE", column6="9999"),
                csv_row(column1=demo.name), csv_row(), csv_row(column1="PRODUCTO FICTICIO qa")]
        preview = self.preview(rows)
        self.assertEqual((preview.new_count, preview.duplicate_count, preview.error_count), (1, 3, 0))
        records = read_csv(csv_upload(rows))
        self.assertEqual(create_from_preview(records, preview.fingerprint), (1, 3))
        self.assertEqual(list(Product.objects.filter(pk__in=[real.pk, demo.pk]).values()), before)
        self.assertEqual(Product.objects.count(), 3)
        repeated = preview_rows(records)
        self.assertEqual(create_from_preview(records, repeated.fingerprint), (0, 4))
        self.assertEqual(Product.objects.count(), 3)

    def test_existing_ambiguous_identity_and_category_block_the_batch(self):
        Product.objects.create(category=self.category, name="Producto ficticio QA", retail_price="1")
        Product.objects.create(category=self.category, name="producto ficticio qa", retail_price="2")
        self.assertEqual(self.preview([csv_row()]).error_count, 1)
        Category.objects.create(name="REPOSTERIA", slug="reposteria-otra")
        self.assertEqual(self.preview([csv_row(column1="Otro")]).error_count, 1)

    def test_conflicting_file_duplicates_are_ambiguous_and_no_row_is_saved(self):
        records = read_csv(csv_upload([csv_row(), csv_row(column6="999")]))
        preview = preview_rows(records)
        self.assertEqual(preview.error_count, 2)
        with self.assertRaises(ValidationError):
            create_from_preview(records, preview.fingerprint)
        self.assertEqual(Product.objects.count(), 0)

    def test_category_or_duplicate_changes_require_another_preview(self):
        records = read_csv(csv_upload([csv_row()]))
        preview = preview_rows(records)
        self.category.name = "REPOSTERÍA"
        self.category.save()
        with self.assertRaises(PreviewChanged):
            create_from_preview(records, preview.fingerprint)
        preview = preview_rows(records)
        Product.objects.create(category=self.category, name="Producto ficticio QA", retail_price="1")
        with self.assertRaises(PreviewChanged) as caught:
            create_from_preview(records, preview.fingerprint)
        self.assertEqual(caught.exception.preview.duplicate_count, 1)
        self.assertEqual(Product.objects.count(), 1)

    def test_modified_contents_cannot_use_the_previous_confirmation(self):
        records = read_csv(csv_upload([csv_row()]))
        preview = preview_rows(records)
        records[0]["values"][6] = "1"
        with self.assertRaises(PreviewChanged):
            create_from_preview(records, preview.fingerprint)
        self.assertEqual(Product.objects.count(), 0)

    def test_rollback_when_a_later_new_row_fails(self):
        records = read_csv(csv_upload([csv_row(), csv_row(column1="Segundo nuevo")]))
        preview = preview_rows(records)
        original_save = Product.save

        def save(product, *args, **kwargs):
            if product.name == "Segundo nuevo":
                raise IntegrityError("Fallo aislado de test")
            return original_save(product, *args, **kwargs)

        with patch.object(Product, "save", save), self.assertRaisesMessage(ValidationError, "Fila 3"):
            create_from_preview(records, preview.fingerprint)
        self.assertEqual(Product.objects.count(), 0)

    def test_limits_headers_malformed_encoding_and_binary_files(self):
        files = [SimpleUploadedFile("bad.txt", b"hello"), SimpleUploadedFile("bad.csv", b"\xff\xfe"),
                 SimpleUploadedFile("bad.csv", b"\x00bad"), SimpleUploadedFile("big.csv", b"a" * (MAX_FILE_BYTES + 1)),
                 SimpleUploadedFile("bad.csv", b"Nombre;Precio\nHola;1"), csv_upload([]),
                 csv_upload([csv_row() for _ in range(MAX_ROWS + 1)]), csv_upload([["x"] * 11]),
                 SimpleUploadedFile("bad.csv", ";".join(HEADERS).encode() + b'\n"unterminated'),
                 SimpleUploadedFile("bad.csv", ";".join([*HEADERS[:-1], "Nombre"]).encode())]
        for upload in files:
            with self.subTest(upload=upload.name), self.assertRaises(ValidationError):
                read_csv(upload)
        self.assertEqual(len(read_csv(csv_upload([csv_row() for _ in range(MAX_ROWS)]))), MAX_ROWS)

    def test_potential_html_and_formula_injection_is_rejected(self):
        for index in (0, 1, 2, 3, 8):
            for value in ('<script>alert(1)</script>', '<img src=x onerror="alert(1)">', "=SUM(1;1)", " +cmd|' /C calc'!A0",
                          "@SUM(1)", "'=SUM(1)", "\ufeff=1", "-1"):
                with self.subTest(index=index, value=value):
                    row = csv_row()
                    row[index] = value
                    self.assertEqual(self.preview([row]).error_count, 1)

    def test_exported_normal_csv_is_compatible_without_updating_existing_products(self):
        from django.contrib.auth import get_user_model
        from django.urls import reverse

        product = Product.objects.create(category=self.category, name="Chocolate QA", retail_price="99.50", quantity_step="1")
        self.client.force_login(get_user_model().objects.create_superuser("csv-export-qa", "", "qa-password"))
        response = self.client.get(reverse("admin:catalog_product_export_csv"))
        records = read_csv(SimpleUploadedFile("export.csv", response.content))
        preview = preview_rows(records)
        self.assertEqual((preview.new_count, preview.duplicate_count, preview.error_count), (0, 1, 0))
        self.assertEqual(create_from_preview(records, preview.fingerprint), (0, 1))
        product.refresh_from_db()
        self.assertEqual(product.retail_price, Decimal("99.50"))
