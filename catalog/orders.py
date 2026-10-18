"""Validación y persistencia atómica de una solicitud confirmada por el cliente."""
import hashlib
import ipaddress
import json
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from django.conf import settings
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.urls import reverse

from .cart import calculate_cart
from .models import BusinessSettings, Category, Order, Product
from .whatsapp import message_configuration, message_label, whatsapp_message, whatsapp_url
from .whatsapp_templates import PRICE_WARNING

SALT = "catalog.order.confirmation.v1"


def public_base_url():
    value = settings.PUBLIC_BASE_URL.rstrip("/")
    try:
        URLValidator(schemes=["http", "https"])(value)
        if len(value) > 400:
            raise ValueError
        parsed = urlsplit(value)
        host = parsed.hostname or ""
        parsed.port  # Validar el puerto.
        try:
            local = not ipaddress.ip_address(host).is_global
        except ValueError:
            local = "." not in host or host.endswith((".local", ".localhost", ".internal"))
        if (not host or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path or parsed.scheme not in ("http", "https")
                or (not settings.ORDER_ALLOW_LOCAL_URLS and (local or parsed.scheme != "https"))):
            raise ValueError
    except (ValueError, ValidationError) as error:
        raise ValidationError(
            "El comercio debe configurar PUBLIC_BASE_URL con una dirección HTTPS pública. "
            "Las pruebas locales requieren ORDER_ALLOW_LOCAL_URLS=1."
        ) from error
    return value


def confirmation_token():
    return signing.dumps(str(uuid4()), salt=SALT)


def confirmation_key(token):
    try:
        return UUID(signing.loads(token, salt=SALT, max_age=None))
    except (signing.BadSignature, ValueError, TypeError) as error:
        raise ValidationError("La revisión venció. Volvé a revisar el carrito.") from error


def request_hash(items, customer, revision):
    value = {"items": items, "customer": customer, "message_revision": revision}
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def saved_order(key, fingerprint):
    order = Order.objects.filter(confirmation_key=key).first()
    if order and order.request_hash != fingerprint:
        raise ValidationError("Esta confirmación ya fue utilizada. Volvé a revisar el carrito.")
    return order


def prepare_order(submitted, customer, token, revision):
    key = confirmation_key(token)
    fingerprint = request_hash(submitted, customer, revision)
    existing = saved_order(key, fingerprint)
    if existing:
        return existing, None, None
    base_url = public_base_url()
    if not settings.WHATSAPP_PHONE:
        raise ValidationError("El comercio todavía no habilitó su número de WhatsApp.")
    with transaction.atomic():
        # Un orden estable de bloqueos evita intercalar cambios de catálogo durante la confirmación.
        ids = [item["id"] for item in submitted]
        category_ids = Product.objects.filter(pk__in=ids).values_list("category_id", flat=True)
        list(Category.objects.filter(pk__in=category_ids).order_by("pk").select_for_update())
        list(Product.objects.filter(pk__in=ids).order_by("pk").select_for_update())
        business = BusinessSettings.objects.select_for_update().first()
        existing = saved_order(key, fingerprint)
        if existing:
            return existing, None, None
        cart = calculate_cart(submitted)
        configuration = message_configuration(business)
        changed = cart["items"] != submitted or revision != configuration["revision"]
        if not cart["valid"] or changed:
            cart["notices"].append("Cambió el catálogo o el mensaje. Revisá nuevamente antes de enviar.")
            return None, cart, configuration
        snapshot = [{
            "product_id": row["product"].pk, "name": row["product"].name,
            "brand": row["product"].brand, "description": row["product"].description,
            "sale_unit": row["product"].sale_unit, "quantity": str(int(row["amount"])),
            "unit_price": str(row["price"]), "subtotal": str(row["subtotal"]),
        } for row in cart["rows"]]
        # get_or_create usa la restricción UNIQUE aun si las dos solicitudes no comparten productos.
        order, created = Order.objects.get_or_create(confirmation_key=key, defaults={
            "request_hash": fingerprint, **customer, "items": snapshot, "total": cart["total"],
        })
        if not created:
            if order.request_hash != fingerprint:
                raise ValidationError("Esta confirmación ya fue utilizada. Volvé a revisar el carrito.")
            return order, None, None
        order.detail_url = base_url + reverse("order_detail", kwargs={"token": order.token})
        body = whatsapp_message(cart, configuration)
        if PRICE_WARNING not in body:
            body += "\n\n" + PRICE_WARNING
        lines = [f"*Pedido: {order.code}*", "", body, "", "*Datos del cliente*",
                 "Nombre completo: " + message_label(order.full_name)]
        if order.delivery_mode == Order.Delivery.DELIVERY:
            lines += ["", "*Envío a domicilio*", "Calle: " + message_label(order.street),
                      "Número: " + message_label(order.number)]
            lines += ["Ciudad: " + message_label(order.city)]
        else:
            lines += ["Modalidad: Retiro en el local"]
        lines += ["", "🔗 Detalle del pedido:", order.detail_url]
        order.message = "\n".join(lines)
        order.whatsapp_url = whatsapp_url(order.message)
        if not order.whatsapp_url:
            raise ValidationError("No se pudo preparar el enlace de WhatsApp.")
        # Finalización dentro de la misma transacción; ningún lector ve una instantánea incompleta.
        Order.objects.filter(pk=order.pk).update(detail_url=order.detail_url, message=order.message,
                                                whatsapp_url=order.whatsapp_url)
        return order, None, None
