import re
from urllib.parse import urlencode

from django.conf import settings

from .templatetags.catalog_format import ars, quantity

PRICE_WARNING = "Los precios mostrados son estimados y pueden cambiar. La disponibilidad y la aplicación del precio mayorista están sujetas a confirmación del comercio por WhatsApp."
SEPARATOR = "────────────"


def message_label(value):
    # Sólo presentación: evita abrir/cerrar estilos o insertar líneas desde un nombre.
    return " ".join(value.split()).translate(str.maketrans({"*": "∗", "_": "＿", "~": "∼", "`": "ˋ"}))


def whatsapp_message(cart):
    if not cart["valid"]:
        return ""
    lines = ["Hola! Quisiera realizar el siguiente pedido:", ""]
    for index, row in enumerate(cart["rows"], 1):
        product = row["product"]
        brand = message_label(product.brand)
        price_type = "mayorista" if row["entry"]["price_type"] == "wholesale" else "minorista"
        amount = quantity(row["amount"]).replace(".", ",")
        lines.append(f"*{index}. {message_label(product.name)}*")
        if brand:
            lines.append(f"- Marca: {brand}")
        lines.extend([
            f"- Precio {price_type}: {ars(row['price'])}/{product.sale_unit}",
            f"- Cantidad: {amount} {product.sale_unit}",
            f"- *Subtotal estimado: {ars(row['subtotal'])}*",
            "", SEPARATOR, "",
        ])
    lines.extend([f"*TOTAL ESTIMADO: {ars(cart['total'])}*", "", PRICE_WARNING, "", "Gracias, espero su respuesta!"])
    return "\n".join(lines)


def whatsapp_url(message):
    phone = settings.WHATSAPP_PHONE
    if not message or not re.fullmatch(r"[1-9][0-9]{7,14}", phone):
        return ""
    return f"https://wa.me/{phone}?{urlencode({'text': message})}"
