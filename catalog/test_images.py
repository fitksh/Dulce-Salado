import tempfile
from io import BytesIO
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.views.static import serve
from PIL import Image

from .admin import ProductAdminForm
from .images import MAX_IMAGE_BYTES, optimize_product_image, validate_product_image
from .models import Category, Product


def upload(size=(40, 30), format="PNG", name="untrusted-name.png"):
    output = BytesIO()
    image = Image.new("RGB", size, "orange")
    image.save(output, format=format)
    return SimpleUploadedFile(name, output.getvalue(), content_type="application/octet-stream")


class ProductImageTests(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.directory.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.category = Category.objects.create(name="Test", slug="test")

    def product(self, image):
        return Product.objects.create(category=self.category, name="Test", retail_price="10", image=image)

    def test_real_format_is_checked_and_filename_is_generated(self):
        product = self.product(upload(size=(1800, 900), name="misleading.txt"))
        self.assertTrue(product.image.name.startswith("products/"))
        self.assertTrue(product.image.name.endswith(".webp"))
        self.assertNotIn("misleading", product.image.name)
        with Image.open(product.image.path) as image:
            self.assertEqual(image.format, "WEBP")
            self.assertEqual(image.size, (1200, 600))
            self.assertFalse(image.getexif())

    def test_invalid_file_is_not_written(self):
        with self.assertRaises(ValidationError):
            self.product(SimpleUploadedFile("fake.png", b"not an image", content_type="image/png"))
        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(list(Path(self.directory.name).rglob("*")), [])

    def test_exif_orientation_is_applied_and_metadata_removed(self):
        output = BytesIO()
        image = Image.new("RGB", (40, 20), "orange")
        exif = Image.Exif()
        exif[274] = 6
        exif[315] = "Private test metadata"
        image.save(output, "JPEG", exif=exif)
        product = self.product(SimpleUploadedFile("photo.jpg", output.getvalue()))
        with Image.open(product.image.path) as optimized:
            self.assertEqual(optimized.size, (20, 40))
            self.assertFalse(optimized.getexif())

    def test_transparency_is_preserved(self):
        output = BytesIO()
        Image.new("RGBA", (10, 10), (255, 0, 0, 0)).save(output, "PNG")
        product = self.product(SimpleUploadedFile("transparent.png", output.getvalue()))
        with Image.open(product.image.path) as optimized:
            self.assertEqual(optimized.getpixel((0, 0))[3], 0)

    def test_size_dimensions_and_format_limits(self):
        for file in (
            SimpleUploadedFile("large.png", b"x" * (MAX_IMAGE_BYTES + 1)),
            upload(size=(6001, 1)), upload(format="GIF"),
        ):
            with self.subTest(name=file.name), self.assertRaises(ValidationError):
                validate_product_image(file)

    def test_admin_rejects_invalid_upload(self):
        form = ProductAdminForm(data={
            "category": self.category.pk, "name": "Test", "sale_unit": "pack", "retail_price": "10",
        }, files={"image": SimpleUploadedFile("fake.png", b"invalid")})
        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)

    def test_replace_clear_and_delete_remove_old_files_after_commit(self):
        product = self.product(upload())
        old = product.image.path
        with self.captureOnCommitCallbacks(execute=True):
            product.image = upload()
            product.save()
        self.assertFalse(Path(old).exists())
        self.assertTrue(Path(product.image.path).exists())
        old = product.image.path
        with self.captureOnCommitCallbacks(execute=True):
            product.image = ""
            product.save()
        self.assertFalse(Path(old).exists())
        product.image = upload()
        product.save()
        old = product.image.path
        with self.captureOnCommitCallbacks(execute=True):
            Product.objects.filter(pk=product.pk).delete()
        self.assertFalse(Path(old).exists())


class ProductPhotoResponseTests(SimpleTestCase):
    def test_optimized_photo_is_served_inline_as_webp(self):
        with tempfile.TemporaryDirectory() as directory:
            photo = optimize_product_image(upload())
            Path(directory, "photo.webp").write_bytes(photo.read())
            response = serve(RequestFactory().get("/media/photo.webp"), "photo.webp", document_root=directory)
            try:
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response["Content-Type"], "image/webp")
                self.assertTrue(response["Content-Disposition"].startswith("inline;"))
                self.assertTrue(b"".join(response.streaming_content).startswith(b"RIFF"))
            finally:
                response.close()
