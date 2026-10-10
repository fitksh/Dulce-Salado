import hashlib
import json
import re
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError

from .models import Product


def product_revision(product):
    values = [product.name, product.brand, product.sale_unit, str(product.quantity_step),
              str(product.retail_price), str(product.wholesale_price), product.wholesale_condition]
    return hashlib.sha256(json.dumps(values, ensure_ascii=False).encode()).hexdigest()[:20]


def parse_items(raw):
    try:
        items = json.loads(raw)
    except (ValueError, TypeError) as error:
        raise ValidationError("No se pudo leer el carrito. Volvé a cargar la página.") from error
    if not isinstance(items, list):
        raise ValidationError("El carrito tiene un formato inválido.")
    seen = set()
    for item in items:
        if (not isinstance(item, dict) or type(item.get("id")) is not int
                or item["id"] <= 0 or item["id"] > 9223372036854775807 or item["id"] in seen):
            raise ValidationError("El carrito contiene identificadores inválidos o repetidos.")
        if not isinstance(item.get("quantity"), str) or len(item["quantity"]) > 20:
            raise ValidationError("El carrito contiene una cantidad inválida.")
        if not isinstance(item.get("price_type"), str) or item["price_type"] not in {"retail", "wholesale"}:
            raise ValidationError("Seleccioná un tipo de precio válido.")
        if not isinstance(item.get("revision", ""), str) or not isinstance(item.get("sale_unit", ""), str):
            raise ValidationError("El carrito contiene referencias inválidas.")
        seen.add(item["id"])
    return items


def calculate_cart(items):
    products = {product.pk: product for product in Product.objects.filter(
        pk__in=[item["id"] for item in items], is_active=True, category__is_active=True,
    ).select_related("category")}
    rows, normalized, notices = [], [], []
    total = Decimal("0.00")
    for item in items:
        entry = {key: item.get(key, "") for key in ("id", "quantity", "price_type", "revision", "sale_unit")}
        product = products.get(item["id"])
        row = {"entry": entry, "product": product, "errors": [], "subtotal": None, "quantity_value": entry["quantity"]}
        if product is None:
            row["errors"].append("Este producto ya no está disponible en el catálogo. Quitalo del carrito.")
        else:
            revision = product_revision(product)
            if entry["revision"] and revision != entry["revision"]:
                notices.append(f"{product.name}: cambió la información del catálogo. Revisá precios, unidad y condiciones actuales.")
            entry["revision"] = revision
            if entry["sale_unit"] and entry["sale_unit"] != product.sale_unit:
                row["errors"].append("Cambió la unidad de venta. Ingresá nuevamente la cantidad para la unidad actual.")
                row["quantity_value"] = ""
            else:
                entry["sale_unit"] = product.sale_unit
            text = entry["quantity"].replace(",", ".")
            if not re.fullmatch(r"[0-9]{1,7}(\.[0-9]{1,2})?", text):
                row["errors"].append("Ingresá una cantidad válida con hasta dos decimales.")
            else:
                amount = Decimal(text)
                if amount <= 0 or amount % product.quantity_step != 0:
                    row["errors"].append(f"La cantidad debe ser positiva y múltiplo de {product.quantity_step} {product.sale_unit}.")
                elif product.sale_unit != "kg" and amount != amount.to_integral_value():
                    row["errors"].append("Unidad y paquete requieren cantidades enteras.")
                else:
                    row["amount"] = amount
            price = product.wholesale_price if entry["price_type"] == "wholesale" else product.retail_price
            row["price"] = price
            if price is None:
                row["errors"].append("El precio mayorista ya no está disponible. Seleccioná minorista para continuar.")
            if not row["errors"]:
                row["subtotal"] = (price * row["amount"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                total += row["subtotal"]
        rows.append(row)
        normalized.append(entry)
    valid = bool(rows) and all(not row["errors"] for row in rows)
    return {"rows": rows, "items": normalized, "notices": notices, "valid": valid,
            "total": total if all(not row["errors"] for row in rows) else None}
