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
from PIL import Image  # noqa: E402

from catalog.models import Category, Product  # noqa: E402


def stop_server(signum, frame):
    raise KeyboardInterrupt


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
            image = BytesIO()
            Image.new("RGB", (600, 400), "#edc399").save(image, "PNG")
            Product.objects.create(
                category=category, name="QA Chocolate (test)", brand="QA Marca",
                description="Producto descartable de prueba; no representa información comercial.",
                sale_unit="kg", quantity_step="0.1", retail_price="100.25", wholesale_price="90.50",
                wholesale_condition="Condición de test, confirmar con el comercio",
                image=SimpleUploadedFile("qa.png", image.getvalue()),
            )
            Product.objects.create(category=other, name="QA Velas (test)", retail_price="25.10")
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
