import csv
from decimal import Decimal
from pathlib import Path

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib import messages as admin_messages
from django.contrib.admin.options import IncorrectLookupParameters
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.forms.models import BaseInlineFormSet
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET, require_http_methods

from .csv_import import HEADERS, PreviewChanged, create_from_preview, preview_rows, read_csv
from .models import BusinessSettings, Category, OpeningInterval, Product
from .pdf import build_catalog_pdf, build_catalog_table_pdf

IMPORT_SALT = "catalog.product.csv-preview"
IMPORT_MAX_AGE = 15 * 60
IMPORT_MAX_TOKEN = 2 * 1024 * 1024


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label="Archivo CSV", widget=forms.ClearableFileInput(attrs={"accept": ".csv,text/csv"}),
                               help_text="UTF-8, separador ;, máximo 256 KiB y 500 filas. Las 10 columnas de la plantilla son obligatorias.")

    def clean_csv_file(self):
        return read_csv(self.cleaned_data["csv_file"])


class CSVConfirmationForm(forms.Form):
    preview_token = forms.CharField(widget=forms.HiddenInput, max_length=IMPORT_MAX_TOKEN)


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["quantity_step"].required = False
        if not self.instance.pk:
            self.initial["quantity_step"] = None

    def clean_quantity_step(self):
        value = self.cleaned_data.get("quantity_step")
        if value is None:
            return Decimal("0.1") if self.cleaned_data.get("sale_unit") == "kg" else Decimal("1")
        return value


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "sort_order", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ["name", "brand", "category", "sale_unit", "retail_price", "wholesale_price", "is_active"]
    list_filter = ["category", "sale_unit", "is_active"]
    search_fields = ["name", "brand"]
    list_select_related = ["category"]
    readonly_fields = ["created_at", "updated_at"]
    change_list_template = "admin/catalog/product/change_list.html"

    def get_urls(self):
        return [
            path("exportar-csv/", self.admin_site.admin_view(self.export_csv), name="catalog_product_export_csv"),
            path("exportar-pdf-con-imagenes/", self.admin_site.admin_view(self.export_pdf),
                 {"include_images": True}, name="catalog_product_export_pdf_images"),
            path("exportar-pdf-sin-imagenes/", self.admin_site.admin_view(self.export_pdf),
                 {"include_images": False}, name="catalog_product_export_pdf_plain"),
            path("exportar-pdf-tabla-compacta/", self.admin_site.admin_view(self.export_pdf),
                 {"include_images": False, "table": True}, name="catalog_product_export_pdf_table_plain"),
            path("exportar-pdf-tabla-con-imagenes/", self.admin_site.admin_view(self.export_pdf),
                 {"include_images": True, "table": True}, name="catalog_product_export_pdf_table_images"),
            path("importar-csv/", self.admin_site.admin_view(self.import_csv), name="catalog_product_import_csv"),
            path("plantilla-csv/", self.admin_site.admin_view(self.csv_template), name="catalog_product_csv_template"),
        ] + super().get_urls()

    def export_queryset(self, request):
        if not self.has_view_or_change_permission(request):
            raise PermissionDenied
        # ChangeList aplica los mismos filtros, búsqueda y orden, sin limitar a una página.
        return self.get_changelist_instance(request).queryset

    @method_decorator(require_GET)
    def export_csv(self, request):
        try:
            products = self.export_queryset(request)
        except IncorrectLookupParameters:
            return HttpResponseBadRequest("Filtros de exportación inválidos.")
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="dulce-y-salado-productos.csv"'
        response.write("\ufeff")
        writer = csv.writer(response, delimiter=";")
        writer.writerow(["Categoría", "Nombre", "Marca", "Descripción", "Unidad de venta", "Incremento de cantidad", "Precio minorista", "Precio mayorista", "Condición mayorista", "Activo"])
        for product in products.iterator():
            writer.writerow([
                csv_text(product.category.name), csv_text(product.name), csv_text(product.brand),
                csv_text(product.description), product.sale_unit, csv_decimal(product.quantity_step),
                csv_decimal(product.retail_price), csv_decimal(product.wholesale_price),
                csv_text(product.wholesale_condition), "Sí" if product.is_active else "No",
            ])
        return response

    @method_decorator(require_GET)
    def csv_template(self, request):
        if not self.has_add_permission(request):
            raise PermissionDenied
        text = (Path(settings.BASE_DIR) / "docs" / "plantilla-productos.csv").read_text(encoding="utf-8")
        response = HttpResponse("\ufeff" + text, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="dulce-y-salado-plantilla-productos.csv"'
        return response

    @method_decorator(require_http_methods(["GET", "POST"]))
    def import_csv(self, request):
        if not self.has_add_permission(request):
            raise PermissionDenied
        upload_form = CSVUploadForm()
        confirmation_form = None
        preview = None
        records = None
        import_errors = []
        if request.method == "POST":
            action = request.POST.get("action")
            if action == "analyze":
                upload_form = CSVUploadForm(request.POST, request.FILES)
                if upload_form.is_valid():
                    records = upload_form.cleaned_data["csv_file"]
                    preview = preview_rows(records)
            elif action == "confirm":
                submitted = CSVConfirmationForm(request.POST)
                if submitted.is_valid():
                    try:
                        data = signing.loads(submitted.cleaned_data["preview_token"], salt=IMPORT_SALT, max_age=IMPORT_MAX_AGE)
                        if data["user_id"] != request.user.pk:
                            raise PermissionDenied
                        records = data["records"]
                        created, omitted = create_from_preview(records, data["fingerprint"])
                    except signing.BadSignature:
                        import_errors.append("La vista previa venció o fue modificada. Volvé a analizar el CSV.")
                    except ValidationError as error:
                        import_errors.extend(error.messages)
                    except PreviewChanged as error:
                        preview = error.preview
                        self.message_user(request, "Los datos cambiaron. Revisá esta nueva vista previa y confirmá nuevamente.",
                                          level=admin_messages.WARNING)
                    else:
                        self.message_user(request, f"Importación completada: {created} productos creados y {omitted} duplicados omitidos."
                                          " No se actualizaron productos existentes.", level=admin_messages.SUCCESS)
                        return redirect(reverse("admin:catalog_product_import_csv"))
                else:
                    import_errors.append("Falta una vista previa válida. Volvé a analizar el CSV.")
            else:
                import_errors.append("Seleccioná Analizar archivo para preparar una vista previa.")
        if preview is not None and not preview.error_count:
            token = signing.dumps({"user_id": request.user.pk, "records": records, "fingerprint": preview.fingerprint},
                                  salt=IMPORT_SALT, compress=False)
            if len(token) <= IMPORT_MAX_TOKEN:
                confirmation_form = CSVConfirmationForm(initial={"preview_token": token})
            else:
                import_errors.append("El lote supera el límite de confirmación. Dividí el CSV y analizalo nuevamente.")
        context = {**self.admin_site.each_context(request), "opts": self.model._meta, "title": "Importar productos desde CSV",
                   "upload_form": upload_form, "confirmation_form": confirmation_form, "preview": preview,
                   "headers": HEADERS, "import_errors": import_errors, "can_view_products": self.has_view_or_change_permission(request)}
        return TemplateResponse(request, "admin/catalog/product/import_csv.html", context)

    @method_decorator(require_GET)
    def export_pdf(self, request, *, include_images, table=False):
        try:
            products = self.export_queryset(request)
        except IncorrectLookupParameters:
            return HttpResponseBadRequest("Filtros de exportación inválidos.")
        builder = build_catalog_table_pdf if table else build_catalog_pdf
        data = builder(products.iterator(), include_images=include_images)
        response = HttpResponse(data, content_type="application/pdf")
        if table:
            variant = "tabla-con-imagenes" if include_images else "tabla-compacta"
        else:
            variant = "con-imagenes" if include_images else "sin-imagenes"
        response["Content-Disposition"] = f'attachment; filename="dulce-y-salado-productos-{variant}.pdf"'
        return response


def csv_text(value):
    # Las comillas CSV no impiden que Excel interprete un texto como fórmula.
    first = value.lstrip(" \t\r\n\v\f\ufeff")[:1]
    return "'" + value if first in {"=", "+", "-", "@"} or value.startswith(("\t", "\r", "\n")) else value


def csv_decimal(value):
    return format(value, "f").replace(".", ",") if value is not None else ""


class OpeningIntervalFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        intervals = sorted(
            (form.cleaned_data["weekday"], form.cleaned_data["opens_at"], form.cleaned_data["closes_at"])
            for form in self.forms if form.cleaned_data and not form.cleaned_data.get("DELETE")
        )
        for previous, current in zip(intervals, intervals[1:]):
            if previous[0] == current[0] and current[1] < previous[2]:
                raise ValidationError("Los intervalos de un mismo día no pueden superponerse.")


class OpeningIntervalInline(admin.TabularInline):
    model = OpeningInterval
    formset = OpeningIntervalFormSet
    extra = 1


@admin.register(BusinessSettings)
class BusinessSettingsAdmin(admin.ModelAdmin):
    inlines = [OpeningIntervalInline]

    def has_add_permission(self, request):
        return super().has_add_permission(request) and not BusinessSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
