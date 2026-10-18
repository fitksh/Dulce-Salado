from django.conf import settings
from django.core.checks import Error, register
from django.core.exceptions import ValidationError

from .orders import public_base_url


@register()
def order_configuration(app_configs, **kwargs):
    if settings.DEBUG and not settings.PUBLIC_BASE_URL:
        return []  # El catálogo sigue disponible; preparar pedidos informa la configuración faltante.
    try:
        public_base_url()
    except ValidationError as error:
        return [Error(error.messages[0], id="catalog.E001")]
    return []
