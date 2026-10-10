from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def ars(value):
    formatted = f"{Decimal(value):,.2f}"
    return "$ " + formatted.replace(",", "_").replace(".", ",").replace("_", ".")


@register.filter
def quantity(value):
    value = format(Decimal(value), "f")
    return value.rstrip("0").rstrip(".") if "." in value else value
