"""Servidor QA con base y media descartables; nunca carga fixtures en la base comercial."""

import os
import signal
import sys
import tempfile
from io import BytesIO
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["DJANGO_DEBUG"] = "1"
os.environ["WHATSAPP_PHONE"] = "5491100000000"  # Fixture interceptada por Playwright.

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402
from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.test.runner import DiscoverRunner  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

from catalog.models import Category, Product  # noqa: E402


def stop_server(signum, frame):
    raise KeyboardInterrupt


def test_photo(size):
    """Bordes y esquinas distinguibles para detectar recorte en capturas QA."""
    photo = Image.new("RGB", size, "#edc399")
    drawing = ImageDraw.Draw(photo)
    width, height = size
    drawing.rectangle((0, 0, width - 1, height - 1), outline="#126877", width=12)
    drawing.rectangle((12, 12, 65, 65), fill="#ad3c0c")
    drawing.rectangle((width - 66, height - 66, width - 13, height - 13), fill="#68384c")
    drawing.text((25, height // 2), f"QA {width} x {height}", fill="#292324", font_size=24)
    drawing.text((18, height - 45), "ETIQUETA JUNTO AL BORDE", fill="#292324", font_size=16)
    image = BytesIO()
    photo.save(image, "PNG")
    return SimpleUploadedFile("qa.png", image.getvalue())


def main():
    settings.DATABASES["default"]["TEST"]["NAME"] = f"dulce_salado_qa_{uuid4().hex[:10]}"
    runner = DiscoverRunner(verbosity=1, interactive=False)
    database = runner.setup_databases()
    signal.signal(signal.SIGTERM, stop_server)
    try:
        with tempfile.TemporaryDirectory() as media:
            settings.MEDIA_ROOT = media
            category = Category.objects.create(name="QA Repostería (test)", slug="qa-reposteria")
            other = Category.objects.create(name="QA Cotillón (test)", slug="qa-cotillon")
            hidden = Category.objects.create(name="QA Oculta", slug="qa-oculta", is_active=False)
            Product.objects.create(
                category=category, name="QA Chocolate (test)", brand="QA Marca",
                description="Producto descartable de prueba; no representa información comercial.",
                sale_unit="kg", quantity_step="1", retail_price="100", wholesale_price="90",
                wholesale_condition="Condición de test, confirmar con el comercio. " + "Datos ficticios de prueba. " * 8,
                image=test_photo((600, 400)),
            )
            Product.objects.create(
                category=other, name="QA Velas (test)", retail_price="25",
                image=test_photo((400, 400)),
            )
            Product.objects.bulk_create([
                Product(category=category, name=f"ZZZ QA Scroll {index:02}", retail_price="1")
                for index in range(10)
            ])
            vertical = Product.objects.get(name="ZZZ QA Scroll 00")
            vertical.image = test_photo((300, 600))
            vertical.save()
            Product.objects.create(category=hidden, name="QA Invisible", retail_price="1")
            Product.objects.create(category=category, name="QA Inactivo", retail_price="1", is_active=False)
            get_user_model().objects.create_superuser("qa-admin", "", "qa-only-password-582")
            print("QA aislado listo: http://127.0.0.1:8001/", flush=True)
            call_command("runserver", "0.0.0.0:8001", use_reloader=False)
    except KeyboardInterrupt:
        pass
    finally:
        runner.teardown_databases(database)


if __name__ == "__main__":
    main()
