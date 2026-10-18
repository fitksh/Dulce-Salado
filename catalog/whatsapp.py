import hashlib
import json
import re
from decimal import Decimal
from types import SimpleNamespace
from urllib.parse import quote, urlencode

from django.conf import settings
from django.core.exceptions import ValidationError

from .models import BusinessSettings
from .templatetags.catalog_format import ars, quantity
from .whatsapp_presentations import presentation_text
from .whatsapp_templates import (
    DEFAULT_MESSAGE_TEMPLATE,
    DEFAULT_PRODUCT_TEMPLATE,
    PRICE_WARNING,
    SEPARATOR,
    render_product_template,
    validate_message_template,
    validate_product_template,
)

__all__ = ["PRICE_WARNING", "SEPARATOR", "message_configuration", "whatsapp_message", "whatsapp_preview", "whatsapp_url"]


def message_configuration(business=None):
    if business is None:
        business = BusinessSettings.objects.only("whatsapp_message_template", "whatsapp_product_template").first()
    values = {}
    for key, field, default, validate in (
        ("message", "whatsapp_message_template", DEFAULT_MESSAGE_TEMPLATE, validate_message_template),
        ("product", "whatsapp_product_template", DEFAULT_PRODUCT_TEMPLATE, validate_product_template),
    ):
        value = getattr(business, field, default)
        try:
            validate(value)
        except ValidationError:
            value = default  # Compatibilidad segura ante datos modificados fuera de Admin.
        values[key] = value.replace("\r\n", "\n").replace("\r", "\n")
    values["revision"] = hashlib.sha256(json.dumps(values, ensure_ascii=False).encode()).hexdigest()[:20]
    return values


def message_label(value):
    # Los datos del catálogo no abren estilos ni agregan líneas al texto del comercio.
    return " ".join(value.split()).translate(str.maketrans({"*": "∗", "_": "＿", "~": "∼", "`": "ˋ"}))


def whatsapp_message(cart, configuration=None):
    if not cart["valid"]:
        return ""
    configuration = configuration if configuration is not None else message_configuration()
    blocks = []
    for index, row in enumerate(cart["rows"], 1):
        product = row["product"]
        values = {
            "numero": str(index), "producto": message_label(product.name), "marca": message_label(product.brand),
            "descripcion": message_label(product.description), "unidad": message_label(product.sale_unit),
            "precio": ars(row["price"]), "cantidad": quantity(row["amount"]).replace(".", ","),
            "subtotal": ars(row["subtotal"]),
            **presentation_text(product.sale_unit, message_label(product.description), row["amount"]),
        }
        blocks.append(render_product_template(configuration["product"], values))
    return configuration["message"].format_map({"productos": "\n\n".join(blocks), "total": ars(cart["total"])}).strip()


def whatsapp_preview(business):
    rows = []
    for name, brand, price, amount, unit in (
        ("Gelatina sin sabor (ejemplo)", "Marca de ejemplo", "1900", "1", "paquete"),
        ("Avena arrollada fina (ejemplo)", "", "2400", "3", "kg"),
    ):
        price, amount = Decimal(price), Decimal(amount)
        rows.append({"product": SimpleNamespace(name=name, brand=brand, description="", sale_unit=unit),
                     "price": price, "amount": amount, "subtotal": price * amount})
    return whatsapp_message({"valid": True, "rows": rows, "total": sum(row["subtotal"] for row in rows)},
                            message_configuration(business))


def whatsapp_url(message):
    phone = settings.WHATSAPP_PHONE
    if not message or not re.fullmatch(r"[1-9][0-9]{7,14}", phone):
        return ""
    # El enlace corto wa.me puede sustituir emojis por U+FFFD al redirigir.
    # Abrir directamente click-to-chat con un único componente UTF-8, sin doble codificación.
    query = urlencode({"phone": phone, "text": message}, quote_via=quote, safe="", encoding="utf-8", errors="strict")
    return f"https://api.whatsapp.com/send?{query}"
