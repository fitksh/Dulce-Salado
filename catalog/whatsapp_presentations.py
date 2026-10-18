"""Texto derivado del pedido; no convierte cantidades ni modifica productos."""
import re

from .templatetags.catalog_format import quantity

PLURALS = {"caja": "cajas", "pack": "packs", "paquete": "paquetes", "bolsa": "bolsas", "unidad": "unidades"}
# No hay contenido estructurado en Product. Reconocer sólo estas formas completas
# de peso/composición; cualquier otro texto se conserva como Presentación aparte.
WEIGHT = r"[0-9]+(?:[.,][0-9]+)?\s*(?:kg|gr\.?|g)"
CONTENTS = rf"(?:{WEIGHT}|[1-9][0-9]*\s+(?:paquetes?|cajas?|bolsas?)(?:\s+de\s+{WEIGHT})?)"


def presentation_text(unit, description, amount):
    description = " ".join(description.split()).strip()
    label = quantity(amount).replace(".", ",")
    price_unit = "100 g" if unit == "100 gr" else unit
    if unit == "100 gr":
        selected = f"{label} {'porción' if amount == 1 else 'porciones'} de 100 g"
        redundant = re.fullmatch(r"(?:porci[oó]n\s+(?:de\s+)?)?100\s*(?:gr\.?|g)\.?", description, re.IGNORECASE)
    elif unit == "kg":
        selected = f"{label} kg"
        redundant = re.fullmatch(r"(?:venta\s+)?por\s+(?:kilogramo|kg)\.?", description, re.IGNORECASE)
    else:
        selected = f"{label} {unit if amount == 1 else PLURALS.get(unit, unit)}"
        match = re.fullmatch(rf"{re.escape(unit)}\s+(?:de\s+)?(?P<content>{CONTENTS})\.?", description, re.IGNORECASE)
        if not match:
            match = re.fullmatch(rf"(?P<content>{WEIGHT})\.?", description, re.IGNORECASE)
        redundant = bool(match)
        if match:
            content = match['content'].lower()
            content = re.sub(r"(?<=\d)\s*(?:gr\.?|g)\b\.?", " g", content)
            content = re.sub(r"(?<=\d)\s*kg\b", " kg", content)
            selected += " de " + content
    return {"cantidad_presentacion": selected, "unidad_precio": price_unit,
            "presentacion_adicional": "" if redundant else description}
