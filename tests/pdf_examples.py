"""Ejemplos ficticios para QA visual, sin consultas ni escrituras de base de datos."""

import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.test import override_settings  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

from catalog.models import Category, Product  # noqa: E402
from catalog.pdf import build_catalog_pdf, build_catalog_table_pdf  # noqa: E402


def main():
    output = Path(".qa/pdfs")
    output.mkdir(parents=True, exist_ok=True)
    category = Category(name="Repostería, dietética y cotillón [QA]")
    with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
        products = []
        for index, size in enumerate(((900, 450), (400, 900), (600, 600))):
            image = Image.new("RGB", size, "#edc399")
            drawing = ImageDraw.Draw(image)
            drawing.rectangle((0, 0, size[0] - 1, size[1] - 1), outline="#126877", width=12)
            drawing.rectangle((12, 12, 65, 65), fill="#ad3c0c")
            drawing.rectangle((size[0] - 66, size[1] - 66, size[0] - 13, size[1] - 13), fill="#68384c")
            drawing.text((25, size[1] // 2), "QA", fill="#292324", font_size=32)
            filename = f"qa-{index}.webp"
            image.save(Path(media) / filename, "WEBP")
            products.append(Product(
                category=category, name=f"[DEMO] {('Chocolate cobertura', 'Frutos secos', 'Velas de cumpleaños')[index]}",
                brand="Marca ficticia Águila", description="Datos ficticios de QA. Foto con cuatro bordes visibles; proporción original.",
                image=filename, sale_unit="kg" if index < 2 else "paquete", retail_price="1234.56", wholesale_price="1000.01",
                wholesale_condition="Desde 3 kg; confirmar con el comercio" if index < 2 else "Desde 6 paquetes; confirmar",
            ))
        products.append(Product(category=category, name="[DEMO] Producto sin foto ni marca", retail_price="25"))
        products.append(Product(category=category, name="[DEMO] Producto inactivo / foto faltante", image="faltante.webp",
                                retail_price="3500", description="Se conserva el registro filtrado; disponibilidad a consultar.", is_active=False))
        (Path(media) / "corrupta.webp").write_bytes(b"invalid image")
        products.append(Product(category=category, name="[DEMO] Foto ilegible y nombre extenso que debe mantenerse completo en el documento",
                                image="corrupta.webp", retail_price="0", wholesale_price="0"))
        products.append(Product(
            category=category, name="[DEMO] Descripción extensa, ñ y acentos",
            description="Descripción de QA extensa, con acentos y texto completo. " * 100 + "FIN DE DESCRIPCIÓN DE QA.",
            retail_price="9999.99", wholesale_price="8500", wholesale_condition="Consulta comercial obligatoria.",
        ))
        for include_images, variant in ((True, "con-imagenes"), (False, "sin-imagenes")):
            path = output / f"catalogo-{variant}.pdf"
            path.write_bytes(build_catalog_pdf(products, include_images=include_images))
            print(f"{path}: {path.stat().st_size} bytes")
        path = output / "catalogo-tabla-compacta.pdf"
        path.write_bytes(build_catalog_table_pdf(products))
        print(f"{path}: {path.stat().st_size} bytes")
        path = output / "catalogo-tabla-con-imagenes.pdf"
        path.write_bytes(build_catalog_table_pdf(products, include_images=True))
        print(f"{path}: {path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
