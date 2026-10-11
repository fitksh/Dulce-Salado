"""Datos manuales de desarrollo; nunca se ejecuta desde startup ni migraciones."""

import hashlib
import json
import os
import tempfile
import unicodedata
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import Category, Product

MANIFEST_NAME = ".seed_demo_catalog.json"
DATA_PATH = Path(__file__).parent.parent / "demo_products.json"


def normalize(value):
    return "".join(char for char in unicodedata.normalize("NFKD", value.strip().casefold()) if not unicodedata.combining(char))


def demo_specs():
    groups = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    for category, rows in groups.items():
        for index, (name, unit, step, retail, wholesale, condition) in enumerate(rows):
            yield category, {
                "name": f"[DEMO] {name}",
                "brand": f"Marca Demo {category}" if index % 3 else "",
                "description": f"{name}. Producto ficticio de demostración; precios de prueba.",
                "sale_unit": unit, "quantity_step": Decimal(step),
                "retail_price": Decimal(retail), "wholesale_price": Decimal(wholesale) if wholesale else None,
                "wholesale_condition": condition, "is_active": True, "image": "",
            }


def fingerprint(product):
    fields = ("pk", "category_id", "name", "brand", "description", "sale_unit", "quantity_step", "retail_price",
              "wholesale_price", "wholesale_condition", "image", "is_active", "created_at", "updated_at")
    values = {field: str(getattr(product, field)) for field in fields}
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


class Command(BaseCommand):
    help = "Simula 45 productos [DEMO] en DEBUG. --apply escribe; --remove simula su limpieza conservadora."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Confirmar las escrituras de la operación indicada.")
        parser.add_argument("--remove", action="store_true", help="Limpiar sólo altas propias intactas; combinar con --apply para borrar.")

    def read_manifest(self, path, names):
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            entries = data["products"]
            if data["version"] != 1 or not isinstance(entries, dict) or not set(entries).issubset(names):
                raise ValueError
            for entry in entries.values():
                if (set(entry) != {"pk", "created_at", "fingerprint"} or type(entry["pk"]) is not int or entry["pk"] <= 0
                        or not isinstance(entry["created_at"], str) or not isinstance(entry["fingerprint"], str)
                        or len(entry["fingerprint"]) != 64):
                    raise ValueError
            return entries
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise CommandError("Manifiesto inválido o ilegible: no se modificó ningún producto. Conservá el archivo para revisión.") from error

    def write_manifest(self, path, entries):
        temporary = None
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as output:
                temporary = output.name
                json.dump({"version": 1, "products": entries}, output, ensure_ascii=False, indent=2)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, path)
        except OSError as error:
            raise CommandError("No se pudo guardar el manifiesto; se revierte la operación de base de datos.") from error
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_demo_catalog sólo está permitido con DEBUG=True.")
        specs = list(demo_specs())
        categories = list(Category.objects.select_for_update().all())
        resolved = {}
        for label, _ in specs:
            if label in resolved:
                continue
            matches = [category for category in categories if normalize(category.name) == normalize(label)]
            if len(matches) != 1 or not matches[0].is_active:
                raise CommandError(f"Categoría {label}: debe existir una única categoría activa con ese nombre. No se escribió nada.")
            resolved[label] = matches[0]
        path = Path(settings.MEDIA_ROOT) / MANIFEST_NAME
        entries = self.read_manifest(path, {spec["name"] for _, spec in specs})
        changed = 0
        preserved = 0
        for label, spec in specs:
            name = spec["name"]
            record = entries.get(name)
            owned = Product.objects.filter(pk=record["pk"]).first() if record else None
            identified = owned is not None and owned.created_at.isoformat() == record["created_at"]
            collisions = Product.objects.filter(name=name)
            if options["remove"]:
                if not identified:
                    if record or collisions.exists():
                        preserved += 1
                    continue
                if owned.name != name or fingerprint(owned) != record["fingerprint"] or collisions.count() != 1:
                    preserved += 1
                    continue
                changed += 1
                self.stdout.write(f"Eliminaría: {name}")
                if options["apply"]:
                    owned.delete()
                    del entries[name]
            else:
                if identified or collisions.exists() or record:
                    preserved += 1
                    continue
                product = Product(category=resolved[label], **spec)
                product.full_clean()
                changed += 1
                self.stdout.write(f"Crearía: {name}")
                if options["apply"]:
                    product.save()
                    product.refresh_from_db()
                    entries[name] = {"pk": product.pk, "created_at": product.created_at.isoformat(), "fingerprint": fingerprint(product)}
        if options["apply"] and changed:
            self.write_manifest(path, entries)
        action = "borrados" if options["remove"] else "creados"
        mode = "APLICADO" if options["apply"] else "SIMULACIÓN SIN ESCRITURAS (usar --apply)"
        self.stdout.write(self.style.SUCCESS(f"{mode}: {changed} productos {action}; {preserved} conservados por existencia, edición o identidad dudosa."))
