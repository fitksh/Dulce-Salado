import re
from urllib.parse import urlencode

from django.conf import settings

from .templatetags.catalog_format import ars, quantity

PRICE_WARNING = "Los precios mostrados son estimados y pueden cambiar. La disponibilidad y la aplicación del precio mayorista están sujetas a confirmación del comercio por WhatsApp."


def whatsapp_message(cart):
    if not cart["valid"]:
        return ""
    lines = ["Hola! Quisiera realizar el siguiente pedido:", ""]
    for row in cart["rows"]:
        product = row["product"]
        brand = f" - Marca {product.brand}" if product.brand else ""
        price_type = "mayorista" if row["entry"]["price_type"] == "wholesale" else "minorista"
        amount = quantity(row["amount"]).replace(".", ",")
        lines.append(
            f"- {product.name}{brand} - precio {price_type} {ars(row['price'])}/{product.sale_unit}"
            f" - cantidad {amount} {product.sale_unit} - subtotal estimado: {ars(row['subtotal'])}"
        )
    lines.extend(["", f"Total estimado: {ars(cart['total'])}", "", PRICE_WARNING, "", "Gracias, espero su respuesta!"])
    return "\n".join(lines)


def whatsapp_url(message):
    phone = settings.WHATSAPP_PHONE
    if not message or not re.fullmatch(r"[1-9][0-9]{7,14}", phone):
        return ""
    return f"https://wa.me/{phone}?{urlencode({'text': message})}"
