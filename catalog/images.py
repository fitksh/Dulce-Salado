from io import BytesIO
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_SIDE = 6000
MAX_IMAGE_PIXELS = 16_000_000


def product_image_path(instance, filename):
    return f"products/{uuid4().hex}.webp"


def validate_product_image(file):
    if file.size > MAX_IMAGE_BYTES:
        raise ValidationError("La imagen debe pesar como máximo 5 MB.")
    try:
        file.seek(0)
        with Image.open(file) as image:
            if image.format not in {"JPEG", "PNG", "WEBP"}:
                raise ValidationError("Usá una imagen JPEG, PNG o WebP.")
            width, height = image.size
            if max(width, height) > MAX_IMAGE_SIDE or width * height > MAX_IMAGE_PIXELS:
                raise ValidationError("La imagen supera 6000 px por lado o 16 megapíxeles.")
            if getattr(image, "n_frames", 1) != 1:
                raise ValidationError("Usá una imagen sin animación.")
            image.verify()
        file.seek(0)
        with Image.open(file) as image:
            image.load()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        raise ValidationError("El archivo no es una imagen válida o está dañado.") from error
    finally:
        file.seek(0)


def optimize_product_image(file):
    validate_product_image(file)
    with Image.open(file) as original:
        image = ImageOps.exif_transpose(original)
        image.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        image = image.convert("RGBA" if "A" in image.getbands() or "transparency" in image.info else "RGB")
        output = BytesIO()
        image.save(output, format="WEBP", quality=82, method=6, exif=b"", icc_profile=b"")
    file.seek(0)
    return ContentFile(output.getvalue(), name="product.webp")
