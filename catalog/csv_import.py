"""CSV de altas: análisis acotado, vista previa sin escrituras y guardado atómico."""

import csv
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from io import StringIO
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from .models import Category, Product

HEADERS = ("Categoría", "Nombre", "Marca", "Descripción", "Unidad de venta", "Incremento de cantidad",
           "Precio minorista", "Precio mayorista", "Condición mayorista", "Activo")
FIELDS = ("category", "name", "brand", "description", "sale_unit", "quantity_step", "retail_price",
          "wholesale_price", "wholesale_condition", "is_active")
MAX_FILE_BYTES = 256 * 1024
MAX_ROWS = 500
MAX_TEXT_LENGTH = 4000
INTEGER_PATTERN = re.compile(r"[0-9]+\Z")
HTML_PATTERN = re.compile(r"<\s*/?\s*[a-zA-Z][^>]*>")
CONTROL_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def normalized(value):
    decomposed = unicodedata.normalize("NFKD", value)
    return " ".join("".join(c for c in decomposed if not unicodedata.combining(c)).casefold().split())


def read_csv(upload):
    if Path(upload.name).suffix.lower() != ".csv":
        raise ValidationError("Seleccioná un archivo con extensión .csv.")
    data = upload.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ValidationError("El CSV supera el límite de 256 KiB. Dividilo en archivos más pequeños.")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValidationError("El CSV debe estar codificado en UTF-8, con o sin BOM.") from error
    if CONTROL_PATTERN.search(text):
        raise ValidationError("El archivo contiene caracteres de control o contenido binario inválido.")
    for separator in (";", ","):
        reader = csv.reader(StringIO(text, newline=""), delimiter=separator, strict=True)
        try:
            headings = tuple(next(reader, ()))
        except csv.Error:
            continue
        if headings != HEADERS:
            continue
        try:
            records = []
            while True:
                number = reader.line_num + 1
                values = next(reader, None)
                if values is None:
                    break
                if not values or not any(value.strip() for value in values):
                    continue
                if len(values) != len(HEADERS):
                    raise ValidationError(f"Fila {number}: se esperaban exactamente 10 columnas.")
                if len(records) >= MAX_ROWS:
                    raise ValidationError("El CSV supera el límite de 500 filas de productos.")
                records.append({"number": number, "values": values})
        except csv.Error as error:
            raise ValidationError("CSV malformado: revisá comillas, columnas y separadores.") from error
        if not records:
            raise ValidationError("El CSV no contiene filas de productos.")
        return records
    raise ValidationError("Encabezados inválidos. Usá las 10 columnas exactas de la plantilla, en el mismo orden.")


@dataclass
class ImportRow:
    number: int
    values: list[str]
    product: Product | None = None
    errors: list[str] = field(default_factory=list)
    duplicate_reason: str = ""
    existing_ids: list[int] = field(default_factory=list)

    @property
    def status(self):
        return "error" if self.errors else "duplicado" if self.duplicate_reason else "nuevo"


@dataclass
class ImportPreview:
    rows: list[ImportRow]

    @property
    def new_count(self):
        return sum(row.status == "nuevo" for row in self.rows)

    @property
    def duplicate_count(self):
        return sum(row.status == "duplicado" for row in self.rows)

    @property
    def error_count(self):
        return sum(row.status == "error" for row in self.rows)

    @property
    def fingerprint(self):
        # Incluye la categoría resuelta y duplicados concretos: no confirmar
        # una vista previa cuya clasificación o identidad cambió entre pasos.
        state = [(row.number, row.values, row.status, row.errors, row.existing_ids,
                  (row.product.category_id, row.product.category.name) if row.product else None)
                 for row in self.rows]
        return hashlib.sha256(json.dumps(state, ensure_ascii=False).encode("utf-8")).hexdigest()


def _decimal(value, label, *, default=None):
    if not value:
        if default is None:
            raise ValidationError(f"{label}: completá el valor obligatorio.")
        return default
    if not INTEGER_PATTERN.fullmatch(value):
        raise ValidationError(f"{label}: usá sólo dígitos, sin decimales ni separador de miles, por ejemplo 14500.")
    return Decimal(value.replace(",", "."))


def _product(values, categories):
    clean = [value.strip() for value in values]
    errors = []
    for label, value in zip(HEADERS, clean):
        first = value.lstrip("\ufeff \t\r\n").lstrip("'")[:1]
        if len(value) > MAX_TEXT_LENGTH:
            errors.append(f"{label}: máximo {MAX_TEXT_LENGTH} caracteres por campo.")
        if first in {"=", "+", "-", "@"} or HTML_PATTERN.search(value) or CONTROL_PATTERN.search(value):
            errors.append(f"{label}: no se admite HTML, fórmulas ni contenido ejecutable.")
    matches = categories.get(normalized(clean[0]), []) if clean[0] else []
    if len(matches) != 1:
        errors.append("Categoría: debe existir previamente con un nombre no ambiguo.")
    if not clean[1]:
        errors.append("Nombre: completá el valor obligatorio.")
    if clean[4] not in Product.SaleUnit.values:
        errors.append("Unidad de venta: usá 100 gr, kg, caja, pack, paquete o bolsa.")
    active = normalized(clean[9])
    if active not in {"", "si", "no", "true", "false", "1", "0"}:
        errors.append("Activo: usá Sí/No, True/False, 1/0 o dejalo vacío para Sí.")
    numbers = {}
    for index, default in ((5, Decimal("1.00")),
                           (6, None), (7, None)):
        try:
            numbers[FIELDS[index]] = None if index == 7 and not clean[index] else _decimal(clean[index], HEADERS[index], default=default)
        except ValidationError as error:
            errors.extend(error.messages)
    if errors:
        raise ValidationError(errors)
    product = Product(category=matches[0], name=clean[1], brand=clean[2], description=clean[3], sale_unit=clean[4],
                      wholesale_condition=clean[8], is_active=active in {"", "si", "true", "1"}, **numbers)
    try:
        product.full_clean()
    except ValidationError as error:
        labels = dict(zip(FIELDS, HEADERS))
        raise ValidationError([f"{labels.get(key, key)}: {message}" for key, messages in error.message_dict.items()
                               for message in messages]) from error
    return product


def preview_rows(records, *, categories=None):
    categories_by_name = defaultdict(list)
    for category in categories if categories is not None else Category.objects.all():
        categories_by_name[normalized(category.name)].append(category)
    existing = defaultdict(list)
    for pk, category_id, name, brand, unit, description in Product.objects.values_list(
        "pk", "category_id", "name", "brand", "sale_unit", "description",
    ).order_by("pk"):
        existing[(category_id, normalized(name), normalized(brand), unit, normalized(description))].append(pk)
    rows, seen = [], {}
    for record in records:
        row = ImportRow(number=record["number"], values=list(record["values"]))
        rows.append(row)
        try:
            row.product = _product(row.values, categories_by_name)
        except ValidationError as error:
            row.errors = error.messages
            continue
        product = row.product
        identity = (product.category_id, normalized(product.name), normalized(product.brand),
                    product.sale_unit, normalized(product.description))
        row.existing_ids = existing.get(identity, [])
        if len(row.existing_ids) > 1:
            row.errors.append("Identidad ambigua: hay varios productos existentes con esta categoría, nombre, marca, unidad y descripción.")
        elif row.existing_ids:
            row.duplicate_reason = "Ya existe un producto con esta categoría, nombre, marca, unidad y descripción. Se omite sin actualizarlo."
        elif identity in seen:
            previous = seen[identity]
            if all(getattr(product, key) == getattr(previous.product, key) for key in FIELDS[3:]):
                row.duplicate_reason = f"Misma identidad y datos que la fila {previous.number}. Se omite."
            else:
                message = f"Identidad ambigua dentro del CSV: datos distintos en las filas {previous.number} y {row.number}."
                previous.errors.append(message)
                row.errors.append(message)
        else:
            seen[identity] = row
    return ImportPreview(rows)


class PreviewChanged(Exception):
    def __init__(self, preview):
        self.preview = preview


@transaction.atomic
def create_from_preview(records, expected_fingerprint):
    # Orden fijo y bloqueos de categorías existentes serializan estas importaciones,
    # sin añadir un modelo/historial ni una nueva regla de unicidad de productos.
    categories = list(Category.objects.select_for_update().order_by("pk"))
    preview = preview_rows(records, categories=categories)
    if preview.fingerprint != expected_fingerprint:
        raise PreviewChanged(preview)
    if preview.error_count:
        raise ValidationError("Hay filas con errores. No se importó ningún producto; corregí y analizá nuevamente el CSV.")
    for row in preview.rows:
        if row.status != "nuevo":
            continue
        try:
            row.product.full_clean()
            row.product.save()
        except (ValidationError, IntegrityError) as error:
            raise ValidationError(f"Fila {row.number}: no pudo guardarse. No se importó ningún producto; volvé a analizar el CSV.") from error
    return preview.new_count, preview.duplicate_count
