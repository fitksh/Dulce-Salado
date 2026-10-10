from decimal import Decimal

from django import forms
from django.contrib import admin

from .models import Category, Product


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
