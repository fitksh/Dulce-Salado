"""Convertir el logo provisto a WebP sin recortar ni ampliar su resolución."""

from pathlib import Path

from PIL import Image, ImageOps

root = Path(__file__).resolve().parent.parent
source = root / "assets/brand/logo-original.jpg"
if not source.exists():
    source = root / "assets/brand/logo-dulce-salado.jpg"
destination = root / "static/img/logo.webp"
destination.parent.mkdir(parents=True, exist_ok=True)
with Image.open(source) as original:
    image = ImageOps.exif_transpose(original).convert("RGB")
    image.thumbnail((300, 300), Image.Resampling.LANCZOS)
    image.save(destination, "WEBP", quality=90, method=6, exif=b"", icc_profile=b"")
print(f"Logo WebP: {image.width}×{image.height} px, {destination.stat().st_size} bytes")
