import hashlib
import json
import re
from decimal import Decimal

from django.core.exceptions import ValidationError

from .models import Product


def product_revision(product):
    values = ["retail-only", product.name, product.brand, product.description, product.sale_unit,
              str(product.quantity_step), str(product.retail_price)]
    return hashlib.sha256(json.dumps(values, ensure_ascii=False).encode()).hexdigest()[:20]


def parse_items(raw):
    try:
        items = json.loads(raw)
    except (ValueError, TypeError) as error:
        raise ValidationError("No se pudo leer el carrito. Volvé a cargar la página.") from error
    if not isinstance(items, list) or len(items) > 200:
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
    total = Decimal("0")
    for item in items:
        entry = {key: item.get(key, "") for key in ("id", "quantity", "price_type", "revision", "sale_unit")}
        product = products.get(item["id"])
        row = {"entry": entry, "product": product, "errors": [], "quantity_error": "", "subtotal": None, "quantity_value": entry["quantity"]}
        if product is None:
            row["errors"].append("Este producto ya no está disponible en el catálogo. Quitalo del carrito.")
        else:
            if entry["price_type"] != "retail":
                notices.append(f"{product.name}: el carrito ahora utiliza el precio publicado. Revisá el importe actualizado antes de continuar.")
            entry["price_type"] = "retail"
            revision = product_revision(product)
            if entry["revision"] and revision != entry["revision"]:
                notices.append(f"{product.name}: cambió la información del catálogo. Revisá el precio y la unidad actuales.")
            entry["revision"] = revision
            if entry["sale_unit"] and entry["sale_unit"] != product.sale_unit:
                row["errors"].append("Cambió la unidad de venta. Ingresá nuevamente la cantidad para la unidad actual.")
                row["quantity_value"] = ""
            else:
                entry["sale_unit"] = product.sale_unit
            text = entry["quantity"].replace(",", ".")
            if re.fullmatch(r"-[0-9]+(\.[0-9]+)?", text) and Decimal(text) < 0:
                row["quantity_error"] = "No se pueden ingresar valores negativos"
            elif not re.fullmatch(r"[0-9]{1,7}(\.[0-9]{1,2})?", text):
                row["quantity_error"] = "Ingresá una cantidad entera válida, sin decimales."
            else:
                amount = Decimal(text)
                if amount != amount.to_integral_value():
                    row["quantity_error"] = "Solo se permiten cantidades enteras, sin decimales."
                elif amount < 1:
                    row["quantity_error"] = "Ingresá una cantidad de al menos 1."
                else:
                    row["amount"] = amount
                    if row["quantity_value"]:
                        row["quantity_value"] = str(int(amount))
            if row["quantity_error"]:
                row["quantity_value"] = ""
                row["errors"].append(row["quantity_error"])
            price = product.retail_price
            row["price"] = price
            row["remove_on_decrease"] = row.get("amount", 0) <= 1 or not row["quantity_value"]
            if not row["errors"]:
                row["subtotal"] = price * row["amount"]
                total += row["subtotal"]
        row["visible_errors"] = [error for error in row["errors"] if error != row["quantity_error"]]
        rows.append(row)
        normalized.append(entry)
    valid = bool(rows) and all(not row["errors"] for row in rows)
    return {"rows": rows, "items": normalized, "notices": notices, "valid": valid,
            "total": total if all(not row["errors"] for row in rows) else None}
