import csv
from decimal import Decimal

from django import forms
from django.contrib import admin
from django.contrib.admin.options import IncorrectLookupParameters
from django.core.exceptions import PermissionDenied, ValidationError
from django.forms.models import BaseInlineFormSet
from django.http import HttpResponse, HttpResponseBadRequest
from django.urls import path
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET

from .models import BusinessSettings, Category, OpeningInterval, Product
from .pdf import build_catalog_pdf, build_catalog_table_pdf


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
    def export_pdf(self, request, *, include_images, table=False):
        try:
            products = self.export_queryset(request)
        except IncorrectLookupParameters:
            return HttpResponseBadRequest("Filtros de exportación inválidos.")
        data = build_catalog_table_pdf(products.iterator()) if table else build_catalog_pdf(products.iterator(), include_images=include_images)
        response = HttpResponse(data, content_type="application/pdf")
        variant = "tabla-compacta" if table else "con-imagenes" if include_images else "sin-imagenes"
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
