import mimetypes

from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "catalog"
    verbose_name = "Catálogo"

    def ready(self):
        # La imagen mínima de Raspberry puede no incluir /etc/mime.types.
        mimetypes.add_type("image/webp", ".webp")
        from . import checks, signals  # noqa: F401
