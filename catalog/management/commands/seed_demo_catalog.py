"""Datos manuales de desarrollo; nunca se ejecuta desde startup ni migraciones."""

import hashlib
import json
import os
import random
import re
import tempfile
import unicodedata
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.images import MAX_IMAGE_BYTES, optimize_product_image, validate_product_image
from catalog.models import Category, Product

MANIFEST_NAME = ".seed_demo_catalog.json"
DATA_PATH = Path(__file__).parent.parent / "demo_products.json"


def demo_images(directory, count):
    """Snapshot validado: sólo archivos inmediatos, nunca enlaces ni originales escritos."""
    try:
        root = Path(directory).resolve(strict=True)
        if not root.is_dir():
            raise CommandError("--images-dir debe indicar un directorio existente y legible.")
        images = []
        for path in sorted(root.iterdir(), key=lambda item: item.name):
            if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                continue
            if path.is_symlink() or path.resolve(strict=True).parent != root:
                raise CommandError(f"Imagen {path.name}: no se permiten enlaces ni archivos fuera del directorio.")
            if path.is_dir():
                continue
            if not path.is_file():
                raise CommandError(f"Imagen {path.name}: debe ser un archivo regular.")
            with path.open("rb") as source:
                content = source.read(MAX_IMAGE_BYTES + 1)
            try:
                validate_product_image(ContentFile(content, name=path.name))
            except ValidationError as error:
                raise CommandError(f"Imagen {path.name} inválida: {'; '.join(error.messages)} No se creó ningún producto.") from error
            images.append((path.name, content))
        if not images:
            raise CommandError("--images-dir no contiene imágenes JPEG, PNG o WebP válidas; no se creó ningún producto.")
    except OSError as error:
        raise CommandError(f"No se pudo leer --images-dir: {error}. No se creó ningún producto.") from error
    # Reparto equilibrado por defecto; el mapa opcional fija fotos por producto.
    generator = random.Random(0)
    generator.shuffle(images)
    assignments = [images[index % len(images)] for index in range(count)]
    generator.shuffle(assignments)
    return assignments


def normalize(value):
    return "".join(char for char in unicodedata.normalize("NFKD", value.strip().casefold()) if not unicodedata.combining(char))


def demo_specs():
    groups = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    for category, rows in groups.items():
        for row in rows:
            name, unit, step, retail, wholesale, condition, metadata = row
            yield category, {
                "name": name, "brand": metadata["brand"], "description": metadata["description"],
                "sale_unit": unit, "quantity_step": Decimal(step),
                "retail_price": Decimal(retail), "wholesale_price": Decimal(wholesale) if wholesale else None,
                "wholesale_condition": condition, "is_active": True, "image": "",
            }


def seed_key(category, spec):
    return json.dumps([normalize(category), spec["name"], spec["sale_unit"], spec["description"]],
                      ensure_ascii=False, separators=(",", ":"))


def mapped_images(path, images, specs):
    try:
        mapping = json.loads(Path(path).read_text(encoding="utf-8"))
        names = {spec["name"] for _, spec in specs}
        if not isinstance(mapping, dict) or set(mapping) != names:
            raise ValueError("El mapa debe incluir exactamente los nombres del seed.")
        sources = dict(images)
        assigned, occurrences = [], {}
        for _, spec in specs:
            name = spec["name"]
            candidates = mapping[name]
            candidates = [candidates] if isinstance(candidates, str) else candidates
            if (not isinstance(candidates, list) or not candidates
                    or any(not isinstance(candidate, str) or candidate not in sources for candidate in candidates)):
                raise ValueError(f"Fotos inexistentes o inválidas para {name}.")
            index = occurrences.get(name, 0)
            source = candidates[index % len(candidates)]
            occurrences[name] = index + 1
            assigned.append((source, sources[source]))
        return assigned
    except (OSError, ValueError, TypeError) as error:
        raise CommandError(f"Mapa de imágenes inválido: {error}. No se escribió ningún producto.") from error


def fingerprint(product):
    fields = ("pk", "category_id", "name", "brand", "description", "sale_unit", "quantity_step", "retail_price",
              "wholesale_price", "wholesale_condition", "image", "is_active", "created_at", "updated_at")
    values = {field: str(getattr(product, field)) for field in fields}
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


class Command(BaseCommand):
    help = "Simula 45 presentaciones de prueba sin prefijo en DEBUG. --apply escribe; --remove simula su limpieza conservadora."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Confirmar las escrituras de la operación indicada.")
        parser.add_argument("--remove", action="store_true", help="Limpiar sólo altas propias intactas; combinar con --apply para borrar.")
        parser.add_argument("--image-map", help="JSON opcional: nombre de producto a archivo(s) del directorio de fotos.")
        parser.add_argument("--images-dir", help="Directorio local de fotos para nuevas altas; reparto reproducible, sin recursión.")

    def read_manifest(self, path, names):
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            entries = data["products"]
            if data["version"] == 1:
                raise CommandError("Manifiesto anterior v1 conservado: no se escribió nada. Respaldá base/media y revisá la carga anterior antes de sustituirlo; no se adopta por nombre.")
            if data["version"] != 2 or not isinstance(entries, dict) or not set(entries).issubset(names):
                raise ValueError
            for entry in entries.values():
                if (set(entry) not in ({"pk", "created_at", "fingerprint"},
                                      {"pk", "created_at", "fingerprint", "image", "image_sha256"})
                        or type(entry["pk"]) is not int or entry["pk"] <= 0
                        or not isinstance(entry["created_at"], str) or not isinstance(entry["fingerprint"], str)
                        or len(entry["fingerprint"]) != 64):
                    raise ValueError
                if "image" in entry and (not isinstance(entry["image"], str)
                                         or not re.fullmatch(r"products/[0-9a-f]{32}\.webp", entry["image"])
                                         or not isinstance(entry["image_sha256"], str)
                                         or not re.fullmatch(r"[0-9a-f]{64}", entry["image_sha256"])):
                    raise ValueError
            return entries
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise CommandError("Manifiesto inválido o ilegible: no se modificó ningún producto. Conservá el archivo para revisión.") from error

    def write_manifest(self, path, entries):
        self.write_manifest_bytes(path, json.dumps({"version": 2, "products": entries}, ensure_ascii=False, indent=2).encode("utf-8"))

    def write_manifest_bytes(self, path, content):
        temporary = None
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, delete=False) as output:
                temporary = output.name
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, path)
        except OSError as error:
            raise CommandError("No se pudo guardar el manifiesto; se revierte la operación de base de datos.") from error
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_demo_catalog sólo está permitido con DEBUG=True.")
        if options["remove"] and options["images_dir"] is not None:
            raise CommandError("--images-dir se usa sólo para crear; la limpieza no necesita el directorio original.")
        if options.get("image_map") and (not options["images_dir"] or options["remove"]):
            raise CommandError("--image-map requiere --images-dir y sólo se utiliza al crear.")
        specs = list(demo_specs())
        images = demo_images(options["images_dir"], len(specs)) if options["images_dir"] is not None else []
        if options.get("image_map"):
            images = mapped_images(options["image_map"], images, specs)
        self.created_images = []
        self.manifest_backup = None
        self.manifest_attempted = False
        self.committed = False
        try:
            with transaction.atomic():
                transaction.on_commit(lambda: setattr(self, "committed", True))
                summary = self.seed_products(specs, images, options)
        except Exception as error:
            if self.committed:
                raise CommandError(f"La base y el manifiesto fueron confirmados, pero falló la limpieza de archivos: {error}.") from error
            # Los archivos no participan de la transacción SQL. Incluye escrituras parciales.
            cleanup_errors = []
            for storage, name in reversed(self.created_images):
                try:
                    storage.delete(name)
                except OSError:
                    cleanup_errors.append(name)
            try:
                if self.manifest_attempted:
                    path = Path(settings.MEDIA_ROOT) / MANIFEST_NAME
                    if self.manifest_backup is None:
                        path.unlink(missing_ok=True)
                    elif not path.exists() or path.read_bytes() != self.manifest_backup:
                        self.write_manifest_bytes(path, self.manifest_backup)
            except (OSError, CommandError):
                cleanup_errors.append(MANIFEST_NAME)
            if cleanup_errors:
                raise CommandError(f"Altas revertidas, pero no se pudieron limpiar/restaurar: {', '.join(cleanup_errors)}. Error: {error}") from error
            if isinstance(error, CommandError):
                raise
            raise CommandError(f"Seed cancelado: {error}. Se revirtieron las altas y sus fotografías.") from error
        self.stdout.write(self.style.SUCCESS(summary))

    def image_owned(self, product, record):
        if not product.image:
            return "image" not in record
        if record.get("image") != product.image.name:
            return False
        if Product.objects.exclude(pk=product.pk).filter(image=product.image.name).exists():
            return False
        path = Path(settings.MEDIA_ROOT) / product.image.name
        try:
            if path.is_symlink() or path.parent.is_symlink():
                return False
            return hashlib.sha256(path.read_bytes()).hexdigest() == record["image_sha256"]
        except OSError:
            return False

    def seed_products(self, specs, images, options):
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
        entries = self.read_manifest(path, {seed_key(label, spec) for label, spec in specs})
        self.manifest_backup = path.read_bytes() if path.exists() else None
        changed = 0
        preserved = 0
        pending = []
        for index, (label, spec) in enumerate(specs):
            name = spec["name"]
            key = seed_key(label, spec)
            record = entries.get(key)
            owned = Product.objects.select_for_update().filter(pk=record["pk"]).first() if record else None
            identified = owned is not None and owned.created_at.isoformat() == record["created_at"]
            collisions = Product.objects.filter(category=resolved[label], name=name, sale_unit=spec["sale_unit"], description=spec["description"])
            if options["remove"]:
                if not identified:
                    if record or collisions.exists():
                        preserved += 1
                    continue
                if (owned.name != name or fingerprint(owned) != record["fingerprint"] or collisions.count() != 1
                        or not self.image_owned(owned, record)):
                    preserved += 1
                    continue
                changed += 1
                self.stdout.write(f"Eliminaría: {name}")
                if options["apply"]:
                    owned.delete()
                    del entries[key]
            else:
                if identified or collisions.exists() or record:
                    preserved += 1
                    continue
                product = Product(category=resolved[label], **spec)
                product.full_clean()
                changed += 1
                self.stdout.write(f"Crearía: {name}")
                if options["apply"]:
                    pending.append((product, images[index] if images else None, key))
        # Todos los datos/imágenes se validan antes de la primera alta o copia.
        for product, source, key in pending:
            image_hash = None
            if source:
                source_name, data = source
                content = optimize_product_image(ContentFile(data, name=source_name))
                field = Product._meta.get_field("image")
                storage = field.storage
                name = field.generate_filename(product, content.name)
                while storage.exists(name):
                    name = field.generate_filename(product, content.name)
                self.created_images.append((storage, name))
                stored = storage.save(name, content)
                if stored != name:
                    self.created_images.append((storage, stored))
                product.image = stored  # Copia ya optimizada; el modelo no vuelve a convertirla.
                content.seek(0)
                image_hash = hashlib.sha256(content.read()).hexdigest()
            product.save()
            product.refresh_from_db()
            entries[key] = {"pk": product.pk, "created_at": product.created_at.isoformat(), "fingerprint": fingerprint(product)}
            if image_hash:
                entries[key].update(image=product.image.name, image_sha256=image_hash)
        if options["apply"] and changed:
            self.manifest_attempted = True
            self.write_manifest(path, entries)
        action = "borrados" if options["remove"] else "creados"
        mode = "APLICADO" if options["apply"] else "SIMULACIÓN SIN ESCRITURAS (usar --apply)"
        return f"{mode}: {changed} productos {action}; {preserved} conservados por existencia, edición o identidad dudosa."
