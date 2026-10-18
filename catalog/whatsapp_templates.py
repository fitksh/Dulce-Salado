"""Formatos de texto de WhatsApp: sólo campos permitidos, sin ejecutar plantillas."""
from string import Formatter

from django.core.exceptions import ValidationError

PRICE_WARNING = "📌 Los precios y la disponibilidad de los productos se confirmarán al procesar el pedido."
SEPARATOR = "────────────"
DEFAULT_MESSAGE_TEMPLATE = (
    "Hola! Quisiera realizar el siguiente pedido 🛍️:\n\n"
    "{productos}\n\n"
    + SEPARATOR + "\n\n*💰 Total: {total}*\n\n" + PRICE_WARNING
)
DEFAULT_PRODUCT_TEMPLATE = (
    "*{numero}. {producto}*\n"
    "Marca: {marca}\n"
    "Cantidad: {cantidad_presentacion}\n"
    "Presentación: {presentacion_adicional}\n"
    "Precio: {precio} por {unidad_precio}\n"
    "*Subtotal: {subtotal}*"
)
MESSAGE_FIELDS = {"productos", "total"}
PRODUCT_FIELDS = {"numero", "producto", "descripcion", "marca", "precio", "unidad", "cantidad", "subtotal", "cantidad_presentacion", "unidad_precio", "presentacion_adicional"}
REQUIRED_PRODUCT_FIELDS = {"producto", "precio", "subtotal"}


def template_fields(value):
    try:
        parts = list(Formatter().parse(value))
    except ValueError as error:
        raise ValidationError("Revisá las llaves: cada campo debe escribirse como {nombre}.") from error
    fields = set()
    for _, field, spec, conversion in parts:
        if field is not None:
            if spec or conversion:
                raise ValidationError("Usá únicamente los campos indicados, sin formatos ni conversiones adicionales.")
            fields.add(field)
    return fields


def validate_template(value, allowed, required):
    if any(ord(char) < 32 and char not in "\n\r\t" for char in value):
        raise ValidationError("El mensaje contiene caracteres de control no permitidos.")
    fields = template_fields(value)
    unknown = fields - allowed
    missing = required - fields
    if unknown:
        raise ValidationError("Campos no reconocidos: %(fields)s.", params={"fields": ", ".join(sorted(unknown))})
    if missing:
        raise ValidationError("Conservá estos campos para completar el pedido: %(fields)s.",
                              params={"fields": ", ".join("{" + field + "}" for field in sorted(missing))})


def validate_message_template(value):
    validate_template(value, MESSAGE_FIELDS, MESSAGE_FIELDS)


def validate_product_template(value):
    validate_template(value, PRODUCT_FIELDS, REQUIRED_PRODUCT_FIELDS)
    fields = template_fields(value)
    if not fields & {"cantidad", "cantidad_presentacion"} or not fields & {"unidad", "unidad_precio", "cantidad_presentacion"}:
        raise ValidationError("Conservá {cantidad_presentacion}, o los campos {cantidad} y {unidad}, para identificar las presentaciones pedidas.")


def render_product_template(template, values):
    lines = []
    for line in template.splitlines():
        # Omitir sólo líneas totalmente opcionales, sin perder nombre ni importes.
        fields = template_fields(line)
        if fields and fields <= {"marca", "descripcion", "presentacion_adicional"} and all(not values[field] for field in fields):
            continue
        lines.append(line.format_map(values))
    return "\n".join(lines).strip()
