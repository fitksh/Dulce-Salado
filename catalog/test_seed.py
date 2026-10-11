import json
import tempfile
from decimal import Decimal
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from .management.commands.seed_demo_catalog import MANIFEST_NAME, demo_specs
from .models import Category, Product


@override_settings(DEBUG=True)
class DemoSeedTests(TestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.media.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.categories = [Category.objects.create(name=name, slug=slug) for name, slug in (
            ("DIETETICA", "dietetica"), ("Cotillón", "cotillon"), ("Repostería", "reposteria"),
        )]
        self.commercial = Product.objects.create(category=self.categories[0], name="Comercial", retail_price="123.45")
        self.manifest = Path(self.media.name) / MANIFEST_NAME

    def seed(self, *args):
        output = StringIO()
        call_command("seed_demo_catalog", *args, stdout=output)
        return output.getvalue()

    def test_default_dry_run_does_not_write_database_or_manifest(self):
        self.assertIn("SIMULACIÓN SIN ESCRITURAS", self.seed())
        self.assertEqual(Product.objects.count(), 1)
        self.assertFalse(self.manifest.exists())

    def test_apply_creates_45_valid_products_15_per_existing_category_without_images(self):
        self.seed("--apply")
        self.assertEqual(Category.objects.count(), 3)
        self.assertEqual(Product.objects.count(), 46)
        demos = Product.objects.exclude(pk=self.commercial.pk)
        for category in self.categories:
            self.assertEqual(demos.filter(category=category).count(), 15)
        self.assertEqual(set(demos.values_list("sale_unit", flat=True)), {"kg", "unidad", "paquete"})
        self.assertEqual(set(demos.filter(sale_unit="kg").values_list("quantity_step", flat=True)), {Decimal("0.10"), Decimal("0.25")})
        self.assertTrue(demos.filter(wholesale_price__isnull=True).exists())
        self.assertGreater(demos.exclude(wholesale_condition="").values("wholesale_condition").distinct().count(), 3)
        for product in demos:
            product.full_clean()
            self.assertTrue(product.name.startswith("[DEMO] "))
            self.assertTrue(product.description)
            self.assertTrue(product.is_active)
            self.assertFalse(product.image)
            self.assertGreater(product.retail_price, 0)
            if product.sale_unit != "kg":
                self.assertEqual(product.quantity_step, 1)
        self.assertEqual(len(json.loads(self.manifest.read_text(encoding="utf-8"))["products"]), 45)

    def test_repeated_apply_preserves_manual_edits_even_after_rename(self):
        self.seed("--apply")
        demo = Product.objects.filter(name__startswith="[DEMO]").first()
        demo.name = "Demo editado manualmente"
        demo.retail_price = "999.99"
        demo.save()
        original_pks = set(Product.objects.values_list("pk", flat=True))
        self.seed("--apply")
        self.assertEqual(set(Product.objects.values_list("pk", flat=True)), original_pks)
        demo.refresh_from_db()
        self.assertEqual(str(demo.retail_price), "999.99")
        self.commercial.refresh_from_db()
        self.assertEqual(str(self.commercial.retail_price), "123.45")

    def test_missing_ambiguous_or_inactive_categories_abort_before_any_writes(self):
        for case in ("missing", "ambiguous", "inactive"):
            with self.subTest(case=case):
                category = self.categories[-1]
                if case == "missing":
                    category.name = "Otra"
                elif case == "inactive":
                    category.is_active = False
                else:
                    duplicate = Category.objects.create(name="REPOSTERIA", slug="duplicada")
                category.save()
                with self.assertRaises(CommandError):
                    self.seed("--apply")
                self.assertEqual(Product.objects.count(), 1)
                self.assertFalse(self.manifest.exists())
                category.name = "Repostería"
                category.is_active = True
                category.save()
                if case == "ambiguous":
                    duplicate.delete()

    def test_production_blocks_all_operations(self):
        with override_settings(DEBUG=False):
            for args in ((), ("--apply",), ("--remove",), ("--remove", "--apply")):
                with self.subTest(args=args), self.assertRaisesMessage(CommandError, "DEBUG=True"):
                    self.seed(*args)
        self.assertEqual(Product.objects.count(), 1)
        self.assertFalse(self.manifest.exists())

    def test_cleanup_requires_apply_and_preserves_commercial_prefix_collisions_and_edits(self):
        _, spec = next(demo_specs())
        collision = Product.objects.create(category=self.categories[0], **spec)
        unrelated = Product.objects.create(category=self.categories[0], name="[DEMO] Comercial ajeno", retail_price=1)
        self.seed("--apply")
        edited = Product.objects.filter(name__startswith="[DEMO]").exclude(pk__in=[collision.pk, unrelated.pk]).first()
        edited.description = "Editado manualmente"
        edited.save()
        before = Product.objects.count()
        self.seed("--remove")
        self.assertEqual(Product.objects.count(), before)
        self.seed("--remove", "--apply")
        self.assertEqual(set(Product.objects.values_list("pk", flat=True)), {self.commercial.pk, collision.pk, unrelated.pk, edited.pk})
        self.seed("--remove", "--apply")
        self.assertEqual(Product.objects.count(), 4)
        self.assertEqual(Category.objects.count(), 3)

    def test_cleanup_preserves_duplicate_names_and_missing_manifest(self):
        self.seed("--apply")
        original = Product.objects.filter(name__startswith="[DEMO]").first()
        clone = Product.objects.create(category=original.category, name=original.name, retail_price=1)
        self.seed("--remove", "--apply")
        self.assertEqual(Product.objects.filter(pk__in=[original.pk, clone.pk]).count(), 2)
        self.manifest.unlink()
        self.seed("--remove", "--apply")
        self.assertEqual(Product.objects.count(), 3)

    def test_manifest_failure_rolls_back_all_new_products(self):
        with patch("catalog.management.commands.seed_demo_catalog.Command.write_manifest", side_effect=CommandError("Sin permiso")):
            with self.assertRaises(CommandError):
                self.seed("--apply")
        self.assertEqual(Product.objects.count(), 1)

    def test_invalid_manifest_aborts_and_reused_id_is_not_owned(self):
        self.manifest.write_text("invalid", encoding="utf-8")
        with self.assertRaises(CommandError):
            self.seed("--apply")
        self.assertEqual(Product.objects.count(), 1)
        self.manifest.unlink()
        self.seed("--apply")
        original = Product.objects.filter(name__startswith="[DEMO]").first()
        pk, name, category = original.pk, original.name, original.category
        original.delete()
        replacement = Product.objects.create(pk=pk, category=category, name=name, retail_price=1)
        self.seed("--remove", "--apply")
        self.assertTrue(Product.objects.filter(pk=replacement.pk).exists())

    def test_unedited_seed_can_be_removed_and_created_again(self):
        self.seed("--apply")
        self.seed("--apply")
        self.assertEqual(Product.objects.count(), 46)
        self.seed("--remove", "--apply")
        self.assertEqual(list(Product.objects.all()), [self.commercial])
        self.seed("--apply")
        self.assertEqual(Product.objects.count(), 46)
