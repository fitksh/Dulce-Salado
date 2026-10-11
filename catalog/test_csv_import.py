import csv
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import Client, TestCase
from django.urls import reverse

from .admin import IMPORT_MAX_AGE, IMPORT_MAX_TOKEN, IMPORT_SALT
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


def csv_upload(rows, *, delimiter=";", bom=True, name="productos.csv", quoting=csv.QUOTE_MINIMAL):
    stream = StringIO(newline="")
    writer = csv.writer(stream, delimiter=delimiter, quoting=quoting)
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

    def test_quoted_headers_in_comma_and_semicolon_files(self):
        for separator in (",", ";"):
            preview = self.preview([csv_row()], delimiter=separator, quoting=csv.QUOTE_ALL)
            self.assertEqual(preview.new_count, 1)
            self.assertEqual(preview.error_count, 0)

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


class CSVImportAdminTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Repostería", slug="reposteria")
        self.real = Product.objects.create(category=self.category, name="Real QA", retail_price="100", brand="Marca QA")
        self.demo = Product.objects.create(category=self.category, name="[DEMO] Existente", retail_price="50", is_active=False)
        self.staff = get_user_model().objects.create_user("csv-import-staff", is_staff=True)
        self.url = reverse("admin:catalog_product_import_csv")
        self.template_url = reverse("admin:catalog_product_csv_template")

    def allow(self, permission="add_product"):
        self.staff.user_permissions.add(Permission.objects.get(codename=permission))
        self.client.force_login(self.staff)

    def analyze(self, rows=None, **options):
        return self.client.post(self.url, {"action": "analyze", "csv_file": csv_upload(rows or [csv_row()], **options)})

    def token(self, response):
        return response.context["confirmation_form"].initial["preview_token"]

    def confirm(self, token, *, follow=False):
        return self.client.post(self.url, {"action": "confirm", "preview_token": token}, follow=follow)

    def test_authentication_permissions_add_only_and_get_post_methods(self):
        for url in (self.url, self.template_url):
            self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.staff)
        for permission in (None, "view_product", "change_product"):
            if permission:
                self.allow(permission)
            self.assertEqual(self.client.get(self.url).status_code, 403)
            self.assertEqual(self.analyze().status_code, 403)
            self.assertEqual(self.client.get(self.template_url).status_code, 403)
            self.staff.user_permissions.clear()
        self.allow()
        self.assertContains(self.client.get(self.url), "Analizar archivo")
        self.assertEqual(self.analyze().status_code, 200)
        for method in ("put", "patch", "delete"):
            self.assertEqual(getattr(self.client, method)(self.url).status_code, 405)
        self.assertEqual(self.client.post(self.template_url).status_code, 405)
        self.staff.is_staff = False
        self.staff.save()
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_import_button_is_visible_only_with_add_permission(self):
        self.allow("view_product")
        url = reverse("admin:catalog_product_changelist")
        self.assertNotContains(self.client.get(url), "Importar CSV")
        self.allow()
        self.assertContains(self.client.get(url), f'href="{self.url}"')

    def test_template_is_utf8_bom_canonical_and_only_contains_fictional_examples(self):
        self.allow()
        before = list(Product.objects.values())
        response = self.client.get(self.template_url)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("plantilla-productos.csv", response["Content-Disposition"])
        rows = list(csv.reader(StringIO(response.content.decode("utf-8-sig")), delimiter=";"))
        self.assertEqual(tuple(rows[0]), HEADERS)
        self.assertTrue(response.content.startswith(b"\xef\xbb\xbf"))
        self.assertTrue(all("[EJEMPLO]" in row[1] and row[0] == "CATEGORÍA EXISTENTE" for row in rows[1:]))
        self.assertTrue(all(len(row) == 10 for row in rows))
        self.assertEqual(list(Product.objects.values()), before)

    def test_preview_writes_nothing_and_confirmation_is_explicit(self):
        self.allow()
        before = list(Product.objects.values())
        response = self.analyze([csv_row(), csv_row(column1=self.real.name, column2=self.real.brand)])
        preview = response.context["preview"]
        self.assertEqual((preview.new_count, preview.duplicate_count, preview.error_count), (1, 1, 0))
        self.assertContains(response, "Confirmar importación")
        self.assertContains(response, "14500,00")
        self.assertEqual(list(Product.objects.values()), before)
        self.client.post(self.url, {"preview_token": self.token(response)})
        self.assertEqual(list(Product.objects.values()), before)
        result = self.confirm(self.token(response), follow=True)
        self.assertContains(result, "1 productos creados y 1 duplicados omitidos")
        created = Product.objects.get(name="Producto ficticio QA")
        self.assertEqual(created.retail_price, Decimal("14500.00"))
        self.assertEqual(created.quantity_step, Decimal("0.10"))
        self.assertIsNone(created.wholesale_price)
        self.assertEqual(created.image.name, "")
        self.assertEqual(list(Product.objects.filter(pk__in=[self.real.pk, self.demo.pk]).values()), before)

    def test_errors_prevent_confirmation_show_row_numbers_and_escape_html(self):
        self.allow()
        response = self.analyze([csv_row(), csv_row(column1='<img src=x onerror="alert(1)">')])
        self.assertEqual(response.context["preview"].error_count, 1)
        self.assertIsNone(response.context["confirmation_form"])
        self.assertNotContains(response, "Confirmar importación")
        self.assertContains(response, "&lt;img")
        self.assertNotContains(response, '<img src=x onerror="alert(1)">')
        self.assertContains(response, '<th scope="row">3</th>')
        self.assertEqual(Product.objects.count(), 2)

    def test_missing_file_unknown_action_invalid_file_and_tokens_report_errors(self):
        self.allow()
        for data in ({"action": "analyze"}, {"action": "something"}, {"action": "confirm"},
                     {"action": "confirm", "preview_token": "modified"},
                     {"action": "confirm", "preview_token": "x" * (IMPORT_MAX_TOKEN + 1)}):
            response = self.client.post(self.url, data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["import_errors"] or response.context["upload_form"].errors)
        self.assertContains(self.analyze(name="bad.txt"), "extensión .csv")
        self.assertEqual(Product.objects.count(), 2)

    def test_signed_data_expiration_modification_other_user_and_removed_permission(self):
        self.allow()
        token = self.token(self.analyze())
        self.assertContains(self.confirm(token + "x"), "fue modificada")
        with patch("django.core.signing.time.time", return_value=0):
            old = self.token(self.analyze())
        self.assertContains(self.confirm(old), "venció")
        data = signing.loads(token, salt=IMPORT_SALT, max_age=IMPORT_MAX_AGE)
        data["user_id"] += 1000
        self.assertEqual(self.confirm(signing.dumps(data, salt=IMPORT_SALT)).status_code, 403)
        self.staff.user_permissions.clear()
        self.assertEqual(self.confirm(token).status_code, 403)
        self.assertEqual(Product.objects.count(), 2)

    def test_csrf_is_required_for_analysis_and_confirmation(self):
        self.allow()
        guarded = Client(enforce_csrf_checks=True)
        guarded.force_login(self.staff)
        guarded.get(self.url)
        self.assertEqual(guarded.post(self.url, {"action": "analyze", "csv_file": csv_upload([csv_row()])}).status_code, 403)
        token = self.token(self.analyze())
        self.assertEqual(guarded.post(self.url, {"action": "confirm", "preview_token": token}).status_code, 403)
        response = guarded.post(self.url, {"action": "analyze", "csv_file": csv_upload([csv_row()]),
                                           "csrfmiddlewaretoken": guarded.cookies["csrftoken"].value})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 2)

    def test_changes_between_steps_show_fresh_preview_and_never_overwrite(self):
        self.allow()
        token = self.token(self.analyze())
        other = Product.objects.create(category=self.category, name="Producto ficticio QA", retail_price="123")
        response = self.confirm(token)
        self.assertContains(response, "Los datos cambiaron")
        self.assertEqual(response.context["preview"].duplicate_count, 1)
        self.assertEqual(Product.objects.count(), 3)
        self.confirm(self.token(response), follow=True)
        other.refresh_from_db()
        self.assertEqual(other.retail_price, Decimal("123"))
        self.assertEqual(Product.objects.count(), 3)

    def test_deleted_duplicate_requires_preview_before_becoming_new(self):
        self.allow()
        token = self.token(self.analyze([csv_row(column1=self.demo.name)]))
        self.demo.delete()
        response = self.confirm(token)
        self.assertContains(response, "Los datos cambiaron")
        self.assertEqual(response.context["preview"].new_count, 1)
        self.assertFalse(Product.objects.filter(name=self.demo.name).exists())

    def test_new_category_ambiguity_between_steps_displays_errors_and_blocks_confirmation(self):
        self.allow()
        token = self.token(self.analyze())
        Category.objects.create(name="REPOSTERIA", slug="reposteria-ambigua")
        response = self.confirm(token)
        self.assertEqual(response.context["preview"].error_count, 1)
        self.assertContains(response, "Categoría: debe existir")
        self.assertContains(response, '<th scope="row">2</th>')
        self.assertNotContains(response, "Confirmar importación")
        self.assertEqual(Product.objects.count(), 2)

    def test_replay_does_not_duplicate_and_success_clears_uploaded_data(self):
        self.allow()
        token = self.token(self.analyze())
        response = self.confirm(token, follow=True)
        self.assertIsNone(response.context["preview"])
        repeated = self.confirm(token)
        self.assertEqual(repeated.context["preview"].duplicate_count, 1)
        self.assertContains(repeated, "Los datos cambiaron")
        self.assertEqual(Product.objects.count(), 3)
        self.assertNotIn("records", self.client.session)

    def test_transaction_failure_has_error_message_and_no_partial_creations(self):
        self.allow()
        token = self.token(self.analyze([csv_row(), csv_row(column1="Fallará QA")]))
        original = Product.save

        def save(product, *args, **kwargs):
            if product.name == "Fallará QA":
                raise IntegrityError("Fallo aislado de test")
            return original(product, *args, **kwargs)

        with patch.object(Product, "save", save):
            self.assertContains(self.confirm(token), "No se importó ningún producto")
        self.assertEqual(Product.objects.count(), 2)

    def test_unicode_batch_near_file_limit_fits_signed_confirmation_and_preserves_rows(self):
        self.allow()
        rows = [csv_row(column1=f"Lote Unicode QA {index:02}", column3="ñ" * 4000) for index in range(30)]
        upload = csv_upload(rows)
        self.assertLessEqual(upload.size, MAX_FILE_BYTES)
        self.assertGreater(upload.size, 230_000)
        response = self.client.post(self.url, {"action": "analyze", "csv_file": upload})
        self.assertEqual(response.context["preview"].new_count, 30)
        token = self.token(response)
        self.assertLessEqual(len(token), IMPORT_MAX_TOKEN)
        self.assertEqual(Product.objects.count(), 2)
        self.assertContains(self.confirm(token, follow=True), "30 productos creados y 0 duplicados omitidos")
        self.assertEqual(Product.objects.filter(name__startswith="Lote Unicode QA").count(), 30)
        self.assertEqual(Product.objects.get(name="Lote Unicode QA 00").description, "ñ" * 4000)
