import hashlib
import json
import tempfile
from collections import Counter
from decimal import Decimal
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from PIL import Image

from .images import optimize_product_image
from .management.commands.seed_demo_catalog import (
    MANIFEST_NAME,
    Command,
    demo_images,
    demo_specs,
    seed_key,
)
from .models import Category, Product


def product_key(product):
    return seed_key(product.category.name, {"name": product.name, "sale_unit": product.sale_unit, "description": product.description})


@override_settings(DEBUG=True)
class DemoSeedTests(TestCase):
    def setUp(self):
        self.sources = tempfile.TemporaryDirectory()
        self.addCleanup(self.sources.cleanup)
        self.images_dir = Path(self.sources.name)
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.media.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.categories = [Category.objects.create(name=name, slug=slug) for name, slug in (
            ("DIETETICA", "dietetica"), ("Cotillón", "cotillon"), ("Repostería", "reposteria"),
        )]
        self.commercial = Product.objects.create(category=self.categories[0], name="Comercial", retail_price="123")
        self.manifest = Path(self.media.name) / MANIFEST_NAME

    def seed(self, *args):
        output = StringIO()
        call_command("seed_demo_catalog", *args, stdout=output)
        return output.getvalue()

    def source(self, name="photo.png", color=(120, 70, 90), size=(64, 40), format="PNG", **options):
        path = self.images_dir / name
        Image.new("RGB", size, color).save(path, format=format, **options)
        return path

    def photos(self):
        for index in range(9):
            format, extension = (("JPEG", ".JPG"), ("PNG", ".png"), ("WEBP", ".webp"))[index % 3]
            self.source(f"photo-{index}{extension}", color=(20 + 25 * index, 70, 90), format=format)
        return {path: path.read_bytes() for path in self.images_dir.iterdir()}

    def with_images(self, *args):
        return self.seed("--images-dir", str(self.images_dir), *args)

    def media_files(self):
        return {str(path.relative_to(self.media.name)): path.read_bytes()
                for path in Path(self.media.name).rglob("*") if path.is_file()}

    def photo_assignment(self):
        return {product_key(product): hashlib.sha256(Path(product.image.path).read_bytes()).hexdigest()
                for product in Product.objects.exclude(pk=self.commercial.pk)}

    def test_default_dry_run_does_not_write_database_or_manifest(self):
        self.assertIn("SIMULACIÓN SIN ESCRITURAS", self.seed())
        self.assertEqual(Product.objects.count(), 1)
        self.assertFalse(self.manifest.exists())

    def test_apply_creates_45_valid_products_per_existing_category_without_images(self):
        self.seed("--apply")
        self.assertEqual(Category.objects.count(), 3)
        self.assertEqual(Product.objects.count(), 46)
        demos = Product.objects.exclude(pk=self.commercial.pk)
        for category in self.categories:
            self.assertEqual(demos.filter(category=category).count(), {"dietetica": 12, "cotillon": 3, "reposteria": 30}[category.slug])
        self.assertEqual(set(demos.values_list("sale_unit", flat=True)), set(Product.SaleUnit.values))
        self.assertEqual(set(demos.values_list("quantity_step", flat=True)), {Decimal("1")})
        self.assertTrue(demos.filter(wholesale_price__isnull=True).exists())
        self.assertGreaterEqual(demos.exclude(wholesale_condition="").values("wholesale_condition").distinct().count(), 3)
        for product in demos:
            product.full_clean()
            self.assertNotIn("[DEMO]", product.name)
            self.assertTrue(product.description)
            self.assertTrue(product.is_active)
            self.assertFalse(product.image)
            self.assertGreater(product.retail_price, 0)
            if product.sale_unit != "kg":
                self.assertEqual(product.quantity_step, 1)
        self.assertEqual(len(json.loads(self.manifest.read_text(encoding="utf-8"))["products"]), 45)

    def test_repeated_apply_preserves_manual_edits_even_after_rename(self):
        self.seed("--apply")
        demo = Product.objects.exclude(pk=self.commercial.pk).first()
        demo.name = "Demo editado manualmente"
        demo.retail_price = "999"
        demo.save()
        original_pks = set(Product.objects.values_list("pk", flat=True))
        self.seed("--apply")
        self.assertEqual(set(Product.objects.values_list("pk", flat=True)), original_pks)
        demo.refresh_from_db()
        self.assertEqual(str(demo.retail_price), "999")
        self.commercial.refresh_from_db()
        self.assertEqual(str(self.commercial.retail_price), "123")

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
        edited = Product.objects.exclude(pk__in=[self.commercial.pk, collision.pk, unrelated.pk]).first()
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
        original = Product.objects.exclude(pk=self.commercial.pk).first()
        clone = Product.objects.create(category=original.category, name=original.name, sale_unit=original.sale_unit, description=original.description, retail_price=1)
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
        original = Product.objects.exclude(pk=self.commercial.pk).first()
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

    def test_images_create_independent_optimized_copies_with_balanced_reproducible_assignment(self):
        originals = self.photos()
        self.with_images("--apply")
        demos = list(Product.objects.exclude(pk=self.commercial.pk))
        first_paths = {product.image.name for product in demos}
        self.assertEqual(len(first_paths), 45)
        distribution = Counter()
        specs = {seed_key(label, spec): spec for label, spec in demo_specs()}
        for product in demos:
            self.assertRegex(product.image.name, r"^products/[0-9a-f]{32}\.webp$")
            for field, expected in specs[product_key(product)].items():
                if field != "image":
                    self.assertEqual(getattr(product, field), expected)
            with Image.open(product.image.path) as photo:
                self.assertEqual(photo.format, "WEBP")
                self.assertEqual(photo.size, (64, 40))
                distribution[round((photo.getpixel((0, 0))[0] - 20) / 25)] += 1
        self.assertEqual(distribution, Counter({index: 5 for index in range(9)}))
        assignment = self.photo_assignment()
        # Nueve fuentes distribuidas en toda la secuencia, no orden de archivos.
        self.assertGreater(len(set(list(assignment.values())[:9])), 1)
        entries = json.loads(self.manifest.read_text(encoding="utf-8"))["products"]
        for product in demos:
            self.assertEqual(entries[product_key(product)]["image"], product.image.name)
            self.assertEqual(entries[product_key(product)]["image_sha256"], assignment[product_key(product)])
        with self.captureOnCommitCallbacks(execute=True):
            self.seed("--remove", "--apply")
        self.assertEqual(list(Product.objects.all()), [self.commercial])
        self.assertEqual(set(self.media_files()), {MANIFEST_NAME})
        self.with_images("--apply")
        self.assertEqual(self.photo_assignment(), assignment)
        self.assertTrue(first_paths.isdisjoint(Product.objects.exclude(pk=self.commercial.pk).values_list("image", flat=True)))
        for path, content in originals.items():
            self.assertEqual(path.read_bytes(), content)

    def test_image_simulation_and_repeated_apply_never_write_or_replace_existing_demos(self):
        originals = self.photos()
        self.assertIn("SIMULACIÓN SIN ESCRITURAS", self.with_images())
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(self.media_files(), {})
        self.seed("--apply")
        before = list(Product.objects.order_by("pk").values())
        files = self.media_files()
        self.with_images("--apply")
        self.assertEqual(list(Product.objects.order_by("pk").values()), before)
        self.assertEqual(self.media_files(), files)
        self.assertFalse(Product.objects.exclude(image="").exists())
        for path, content in originals.items():
            self.assertEqual(path.read_bytes(), content)

    def test_image_seed_idempotence_and_edit_preservation(self):
        self.photos()
        self.with_images("--apply")
        demo = Product.objects.exclude(pk=self.commercial.pk).first()
        demo.name = "Demo renombrado con foto"
        demo.retail_price = "999"
        demo.save()
        before = list(Product.objects.order_by("pk").values())
        files = self.media_files()
        self.with_images("--apply")
        self.assertEqual(list(Product.objects.order_by("pk").values()), before)
        self.assertEqual(self.media_files(), files)

    def test_one_image_is_copied_45_times_and_modifying_one_copy_leaves_others_and_source_intact(self):
        path = self.source()
        original = path.read_bytes()
        self.with_images("--apply")
        demos = list(Product.objects.exclude(pk=self.commercial.pk))
        self.assertEqual(len({product.image.name for product in demos}), 45)
        other_path = Path(demos[1].image.path)
        other_bytes = other_path.read_bytes()
        Path(demos[0].image.path).write_bytes(b"copia editada manualmente")
        self.assertEqual(other_path.read_bytes(), other_bytes)
        self.assertEqual(path.read_bytes(), original)
        with self.captureOnCommitCallbacks(execute=True):
            self.seed("--remove", "--apply")
        self.assertEqual(set(Product.objects.values_list("pk", flat=True)), {self.commercial.pk, demos[0].pk})
        self.assertTrue(Path(demos[0].image.path).exists())
        self.assertEqual(path.read_bytes(), original)

    def test_invalid_directories_and_nonrecursive_empty_directory_abort_before_writes(self):
        file = self.images_dir / "not-a-directory.txt"
        file.write_text("test")
        nested = self.images_dir / "nested"
        nested.mkdir()
        Image.new("RGB", (10, 10)).save(nested / "valid.png")
        for directory in (self.images_dir / "missing", file, self.images_dir):
            with self.subTest(directory=directory), self.assertRaises(CommandError):
                self.seed("--images-dir", str(directory), "--apply")
            self.assertEqual(Product.objects.count(), 1)
            self.assertEqual(self.media_files(), {})

    def test_any_invalid_candidate_aborts_the_batch_even_with_a_valid_image(self):
        self.source("valid.png")
        invalid = self.images_dir / "invalid.png"
        for case in ("corrupt", "format", "size", "dimensions", "animation"):
            with self.subTest(case=case):
                if case == "corrupt":
                    invalid.write_bytes(b"not an image")
                elif case == "format":
                    self.source(invalid.name, format="GIF")
                elif case == "size":
                    invalid.write_bytes(b"x" * (5 * 1024 * 1024 + 1))
                elif case == "dimensions":
                    self.source(invalid.name, size=(6001, 1))
                else:
                    Image.new("RGB", (10, 10)).save(invalid, "PNG", save_all=True,
                                                  append_images=[Image.new("RGB", (10, 10), "orange")])
                original = invalid.read_bytes()
                with self.assertRaisesMessage(CommandError, "invalid.png"):
                    self.with_images("--apply")
                self.assertEqual(Product.objects.count(), 1)
                self.assertEqual(self.media_files(), {})
                self.assertEqual(invalid.read_bytes(), original)

    def test_links_outside_directory_are_rejected_and_unreadable_inputs_abort(self):
        with tempfile.TemporaryDirectory() as outside:
            original = Path(outside) / "original.png"
            Image.new("RGB", (10, 10)).save(original)
            content = original.read_bytes()
            link = self.images_dir / "link.png"
            link.symlink_to(original)
            with self.assertRaisesMessage(CommandError, "enlaces"):
                self.with_images("--apply")
            self.assertEqual(original.read_bytes(), content)
            link.unlink()
        self.source()
        open_path = Path.open

        def unreadable_source(path, *args, **kwargs):
            if path.parent == self.images_dir:
                raise PermissionError("sin permiso")
            return open_path(path, *args, **kwargs)

        with patch("pathlib.Path.open", unreadable_source):
            with self.assertRaisesMessage(CommandError, "No se pudo leer"):
                self.with_images("--apply")
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(self.media_files(), {})

    def test_database_failure_rolls_back_new_products_images_and_preserves_existing_files(self):
        originals = self.photos()
        self.commercial.image = ContentFile(next(iter(originals.values())), name="commercial.png")
        self.commercial.save()
        files = self.media_files()
        save = Product.save
        calls = 0

        def fail_third(product, *args, **kwargs):
            nonlocal calls
            calls += 1
            save(product, *args, **kwargs)
            if calls == 3:
                raise RuntimeError("fallo de base de prueba")

        with patch.object(Product, "save", fail_third):
            with self.assertRaisesMessage(CommandError, "fallo de base"):
                self.with_images("--apply")
        self.assertEqual(list(Product.objects.all()), [self.commercial])
        self.assertEqual(self.media_files(), files)
        for path, content in originals.items():
            self.assertEqual(path.read_bytes(), content)

    def test_partial_storage_write_is_removed_on_failure(self):
        self.source()
        storage = Product._meta.get_field("image").storage

        def fail_after_partial_write(name, content):
            path = Path(storage.path(name))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"archivo parcial de prueba")
            raise OSError("SSD sin espacio")

        with patch.object(storage, "save", side_effect=fail_after_partial_write):
            with self.assertRaisesMessage(CommandError, "SSD sin espacio"):
                self.with_images("--apply")
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(self.media_files(), {})

    def test_manifest_failure_removes_all_new_copies_and_restores_previous_manifest_bytes(self):
        self.source()
        previous = b'{"version":2,"products":{}}\n'
        self.manifest.write_bytes(previous)
        write = Command.write_manifest

        def fail_after_replace(command, path, entries):
            write(command, path, entries)
            raise CommandError("fallo después del reemplazo")

        with patch.object(Command, "write_manifest", fail_after_replace):
            with self.assertRaisesMessage(CommandError, "después del reemplazo"):
                self.with_images("--apply")
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(self.media_files(), {MANIFEST_NAME: previous})

    def test_cleanup_preserves_shared_photos_collisions_modified_demos_and_originals(self):
        originals = self.photos()
        self.with_images("--apply")
        demos = list(Product.objects.exclude(pk=self.commercial.pk))
        shared, edited, duplicated = demos[:3]
        Product.objects.filter(pk=self.commercial.pk).update(image=shared.image.name)
        edited.description = "Demo modificado"
        edited.save()
        clone = Product.objects.create(category=duplicated.category, name=duplicated.name, sale_unit=duplicated.sale_unit, description=duplicated.description, retail_price=1)
        unrelated = Product.objects.create(category=self.categories[0], name="[DEMO] Ajeno", retail_price=1)
        before = self.media_files()
        self.seed("--remove")
        self.assertEqual(self.media_files(), before)
        self.assertEqual(Product.objects.count(), 48)
        with self.captureOnCommitCallbacks(execute=True):
            self.seed("--remove", "--apply")
        self.assertEqual(set(Product.objects.values_list("pk", flat=True)),
                         {self.commercial.pk, shared.pk, edited.pk, duplicated.pk, clone.pk, unrelated.pk})
        self.assertEqual(set(self.media_files()), {MANIFEST_NAME, shared.image.name, edited.image.name, duplicated.image.name})
        for path, content in originals.items():
            self.assertEqual(path.read_bytes(), content)

    def test_cleanup_failure_keeps_products_manifest_and_copies(self):
        self.source()
        self.with_images("--apply")
        before = self.media_files()
        with self.captureOnCommitCallbacks(execute=True):
            with patch("catalog.management.commands.seed_demo_catalog.Command.write_manifest", side_effect=CommandError("sin permiso")):
                with self.assertRaises(CommandError):
                    self.seed("--remove", "--apply")
        self.assertEqual(Product.objects.count(), 46)
        self.assertEqual(self.media_files(), before)

    def test_image_operations_require_debug_and_remove_does_not_accept_images_dir(self):
        self.source()
        with override_settings(DEBUG=False):
            for apply in ((), ("--apply",)):
                with self.assertRaisesMessage(CommandError, "DEBUG=True"):
                    self.with_images(*apply)
        with self.assertRaisesMessage(CommandError, "sólo para crear"):
            self.with_images("--remove", "--apply")
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(self.media_files(), {})

    def test_optimization_failure_reverts_previously_saved_copies(self):
        path = self.source()
        original = path.read_bytes()
        calls = 0

        def fail_third(content):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise OSError("fallo de conversión")
            return optimize_product_image(content)

        with patch("catalog.management.commands.seed_demo_catalog.optimize_product_image", fail_third):
            with self.assertRaisesMessage(CommandError, "fallo de conversión"):
                self.with_images("--apply")
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(self.media_files(), {})
        self.assertEqual(path.read_bytes(), original)

    def test_large_pool_selects_45_distinct_sources_reproducibly_and_ignores_other_files(self):
        for index in range(46):
            self.source(f"photo-{index:02}.png")
        (self.images_dir / "notes.txt").write_text("not an image")
        assignments = demo_images(str(self.images_dir), 45)
        self.assertEqual(len({name for name, _ in assignments}), 45)
        self.assertEqual(demo_images(str(self.images_dir), 45), assignments)
        self.assertIn("45 productos creados", self.with_images())
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(self.media_files(), {})

    def test_image_pipeline_respects_exif_resize_and_transparency(self):
        exif = Image.Exif()
        exif[274] = 6
        exif[315] = "Metadata privada de prueba"
        self.source("oriented.jpeg", size=(1800, 2), format="JPEG", exif=exif)
        Image.new("RGBA", (10, 10), (255, 0, 0, 0)).save(self.images_dir / "transparent.png")
        self.with_images("--apply")
        kinds = set()
        for product in Product.objects.exclude(pk=self.commercial.pk):
            with Image.open(product.image.path) as photo:
                self.assertFalse(photo.getexif())
                self.assertLessEqual(max(photo.size), 1200)
                if photo.size == (10, 10):
                    self.assertEqual(photo.getpixel((0, 0))[3], 0)
                    kinds.add("transparent")
                else:
                    self.assertEqual(photo.size, (1, 1200))
                    kinds.add("oriented")
        self.assertEqual(kinds, {"transparent", "oriented"})

    def test_same_title_presentations_are_independent_idempotent_and_removable(self):
        self.seed("--apply")
        rows = list(Product.objects.filter(name="Baño de repostería blanco"))
        self.assertEqual(len(rows), 6)
        self.assertTrue({"100 gr", "kg", "paquete"} <= {row.sale_unit for row in rows})
        self.assertEqual(len({row.pk for row in rows}), 6)
        self.assertEqual(len({row.description for row in rows}), 6)
        before = list(Product.objects.order_by("pk").values())
        self.seed("--apply")
        self.assertEqual(list(Product.objects.order_by("pk").values()), before)
        self.seed("--remove", "--apply")
        self.assertEqual(list(Product.objects.all()), [self.commercial])

    def test_legacy_manifest_is_preserved_and_never_adopted_by_name(self):
        original = json.dumps({"version": 1, "products": {}})
        self.manifest.write_text(original)
        with self.assertRaisesMessage(CommandError, "anterior v1 conservado"):
            self.seed("--apply")
        self.assertEqual(self.manifest.read_text(), original)
        self.assertEqual(list(Product.objects.all()), [self.commercial])

    def test_image_map_matches_repeated_presentations_and_rejects_missing_files(self):
        source = self.source("white.png")
        other = self.source("other.png", color=(10, 20, 30))
        mapping = {spec["name"]: other.name for _, spec in demo_specs()}
        mapping["Baño de repostería blanco"] = [source.name]
        path = self.images_dir / "map.json"
        path.write_text(json.dumps(mapping))
        self.with_images("--image-map", str(path), "--apply")
        photos = list(Product.objects.filter(name="Baño de repostería blanco"))
        self.assertEqual(len({row.image.name for row in photos}), 6)
        self.assertEqual(len({Path(row.image.path).read_bytes() for row in photos}), 1)
        self.assertNotEqual(Path(photos[0].image.path).read_bytes(), Path(Product.objects.get(name="Pasta de maní natural", sale_unit="kg").image.path).read_bytes())
        mapping["Baño de repostería blanco"] = "../missing.png"
        path.write_text(json.dumps(mapping))
        before = self.media_files()
        with self.assertRaisesMessage(CommandError, "Mapa de imágenes inválido"):
            self.with_images("--image-map", str(path), "--apply")
        self.assertEqual(self.media_files(), before)
