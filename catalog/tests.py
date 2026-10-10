from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse

from .admin import ProductAdminForm
from .models import Category, Product


class ProductTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Prueba", slug="prueba")

    def product(self, **kwargs):
        return Product(category=self.category, name="Producto de test", retail_price=Decimal("10.25"), **kwargs)

    def test_decimal_prices_and_optional_wholesale(self):
        product = self.product()
        product.full_clean()
        product.save()
        product.refresh_from_db()
        self.assertEqual(product.retail_price, Decimal("10.25"))
        self.assertIsNone(product.wholesale_price)
        self.assertEqual(str(product), product.name)

    def test_invalid_prices_steps_and_units(self):
        for changes in (
            {"retail_price": Decimal("-1")}, {"wholesale_price": Decimal("-1")},
            {"quantity_step": Decimal("0")}, {"quantity_step": Decimal("0.1")},
            {"sale_unit": "gramos"}, {"sale_unit": "paquete", "quantity_step": Decimal("1.5")},
        ):
            with self.subTest(changes=changes):
                product = self.product()
                for key, value in changes.items():
                    setattr(product, key, value)
                with self.assertRaises(ValidationError):
                    product.full_clean()

    def test_kg_accepts_decimal_increment(self):
        self.product(sale_unit="kg", quantity_step=Decimal("0.1")).full_clean()

    def test_database_prevents_negative_price(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            product = self.product()
            product.retail_price = Decimal("-1")
            product.save()

    def test_category_with_products_cannot_be_deleted(self):
        self.product().save()
        with self.assertRaises(ProtectedError):
            self.category.delete()

    def test_admin_default_increment_matches_unit(self):
        for unit, expected in (("kg", "0.1"), ("unidad", "1"), ("paquete", "1")):
            form = ProductAdminForm(data={
                "category": self.category.pk, "name": "Test", "sale_unit": unit,
                "quantity_step": "", "retail_price": "100.50", "is_active": True,
            })
            self.assertTrue(form.is_valid(), form.errors)
            self.assertEqual(form.save().quantity_step, Decimal(expected))


class CatalogAdminTests(TestCase):
    def test_staff_requires_product_permission(self):
        staff = get_user_model().objects.create_user(username="catalog-staff", is_staff=True)
        self.client.force_login(staff)
        url = reverse("admin:catalog_product_changelist")
        self.assertEqual(self.client.get(url).status_code, 403)
        staff.user_permissions.add(Permission.objects.get(codename="view_product"))
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:catalog_product_add")).status_code, 403)

    def test_superuser_can_create_category_and_product(self):
        owner = get_user_model().objects.create_superuser(username="owner", email="", password="test")
        self.client.force_login(owner)
        response = self.client.post(reverse("admin:catalog_category_add"), {
            "name": "Test", "slug": "test", "sort_order": 0, "is_active": True,
        })
        self.assertEqual(response.status_code, 302)
        response = self.client.post(reverse("admin:catalog_product_add"), {
            "category": Category.objects.get().pk, "name": "Test", "sale_unit": "kg",
            "quantity_step": "", "retail_price": "99.99", "is_active": True,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Product.objects.get().quantity_step, Decimal("0.10"))
