from decimal import ROUND_DOWN, Decimal

from django import template

register = template.Library()


@register.filter
def ars(value):
    pesos = Decimal(value).quantize(Decimal("1"), rounding=ROUND_DOWN)
    return "$ " + format(pesos, ",.0f").replace(",", ".")


@register.filter
def quantity(value):
    value = format(Decimal(value), "f")
    return value.rstrip("0").rstrip(".") if "." in value else value


@register.filter
def order_presentation(value):
    """Envolver el texto histórico sólo al mostrarlo; nunca marcar HTML como seguro."""
    if not value or not value.strip():
        return ""
    if value.strip().startswith("(") and value.strip().endswith(")"):
        return value
    return f"({value})"
