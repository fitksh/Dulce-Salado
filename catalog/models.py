from decimal import Decimal
from urllib.parse import urlencode, urlsplit
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction

from .images import optimize_product_image, product_image_path, validate_product_image
from .whatsapp_templates import (
    DEFAULT_MESSAGE_TEMPLATE,
    DEFAULT_PRODUCT_TEMPLATE,
    validate_message_template,
    validate_product_template,
)


class Category(models.Model):
    name = models.CharField("nombre", max_length=100)
    slug = models.SlugField("identificador en URL", unique=True)
    sort_order = models.PositiveIntegerField("orden", default=0)
    is_active = models.BooleanField("activa", default=True)

    class Meta:
        ordering = ["sort_order", "name", "pk"]
        verbose_name = "categoría"
        verbose_name_plural = "categorías"

    def __str__(self):
        return self.name


class Product(models.Model):
    class SaleUnit(models.TextChoices):
        HUNDRED_GRAMS = "100 gr", "100 gr"
        KG = "kg", "kg"
        BOX = "caja", "caja"
        PACK = "pack", "pack"
        PACKAGE = "paquete", "paquete"
        BAG = "bolsa", "bolsa"

    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name="categoría")
    name = models.CharField("nombre", max_length=180)
    brand = models.CharField("marca", max_length=100, blank=True)
    description = models.TextField("descripción", blank=True)
    sale_unit = models.CharField("unidad de venta", max_length=10, choices=SaleUnit.choices, default=SaleUnit.KG)
    quantity_step = models.DecimalField(
        "incremento de cantidad", max_digits=9, decimal_places=2, default=Decimal("1"),
        editable=False,
        validators=[MinValueValidator(Decimal("1")), MaxValueValidator(Decimal("1"))],
        help_text="Siempre una presentación por vez.",
    )
    retail_price = models.DecimalField(
        "precio minorista (ARS)", max_digits=12, decimal_places=0,
        validators=[MinValueValidator(Decimal("0"))],
    )
    wholesale_price = models.DecimalField(
        "precio mayorista (ARS)", max_digits=12, decimal_places=0, blank=True, null=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    wholesale_condition = models.CharField("condición mayorista", max_length=300, blank=True)
    image = models.ImageField(
        "imagen", upload_to=product_image_path, blank=True, validators=[validate_product_image],
        help_text="JPEG, PNG o WebP; máximo 5 MB, 6000 px por lado y 16 MP. Se guarda como WebP hasta 1200 px, sin metadatos.",
    )
    is_active = models.BooleanField("activo", default=True)
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ["name", "pk"]
        verbose_name = "producto"
        verbose_name_plural = "productos"
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity_step=1), name="product_fixed_step"),
            models.CheckConstraint(condition=models.Q(retail_price__gte=0), name="product_nonnegative_retail"),
            models.CheckConstraint(
                condition=models.Q(wholesale_price__isnull=True) | models.Q(wholesale_price__gte=0),
                name="product_nonnegative_wholesale",
            ),
            models.CheckConstraint(condition=models.Q(sale_unit__in=["100 gr", "kg", "caja", "pack", "paquete", "bolsa", "unidad"]), name="product_valid_unit"),
        ]

    def has_legacy_unit(self):
        return self.pk is not None and type(self).objects.filter(pk=self.pk, sale_unit="unidad").exists()

    def clean_fields(self, exclude=None):
        # Las altas sólo usan las seis presentaciones. Una unidad anterior no se
        # convierte a paquete ni cambia de precio sin decisión del administrador.
        exclude = set(exclude or ())
        if self.sale_unit == "unidad" and self.has_legacy_unit():
            exclude.add("sale_unit")
        super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()
        if self.quantity_step != Decimal("1"):
            raise ValidationError({"quantity_step": "El incremento de cantidad debe ser siempre 1."})
        if self.sale_unit == "unidad" and not self.has_legacy_unit():
            raise ValidationError({"sale_unit": "Elegí 100 gr, kg, caja, pack, paquete o bolsa."})

    def __str__(self):
        return f"{self.name} — {self.brand}" if self.brand else self.name

    def save(self, *args, **kwargs):
        if self.sale_unit == "unidad" and not self.has_legacy_unit():
            raise ValidationError({"sale_unit": "Unidad sólo se conserva en productos anteriores."})
        update_fields = kwargs.get("update_fields")
        # Evitar que numeric(12, 0) redondee silenciosamente una escritura del modelo.
        for name in ("retail_price", "wholesale_price"):
            if update_fields is None or name in update_fields:
                value = getattr(self, name)
                if value is not None:
                    value = self._meta.get_field(name).to_python(value)
                    if value != value.to_integral_value():
                        raise ValidationError({name: "Ingresá un precio en pesos enteros, sin decimales."})
        if update_fields is not None and "image" not in update_fields:
            return super().save(*args, **kwargs)
        previous = type(self).objects.filter(pk=self.pk).values_list("image", flat=True).first() if self.pk else None
        if self.image and not self.image._committed:
            self.image = optimize_product_image(self.image)
        super().save(*args, **kwargs)
        if previous and previous != self.image.name:
            storage = self._meta.get_field("image").storage
            transaction.on_commit(lambda: storage.delete(previous))


class BusinessSettings(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    address = models.CharField("dirección comercial", max_length=300, blank=True)
    maps_url = models.URLField(
        "enlace exacto de Google Maps", max_length=500, blank=True,
        help_text="Opcional: enlace HTTPS compartido desde Google Maps. Sin enlace se busca la dirección.",
    )
    hours_initialized = models.BooleanField(
        "publicar horario semanal", default=False,
        help_text="Activar después de completar los intervalos. Los días sin intervalos se publicarán como cerrados.",
    )

    whatsapp_message_template = models.TextField(
        "mensaje general de WhatsApp", default=DEFAULT_MESSAGE_TEMPLATE, max_length=5000,
        validators=[validate_message_template],
        help_text="Cambiá frases, emojis y orden. Conservá {productos} para el listado y {total} para el importe calculado. Los campos se completan automáticamente con el carrito.",
    )
    whatsapp_product_template = models.TextField(
        "formato de cada producto", default=DEFAULT_PRODUCT_TEMPLATE, max_length=3000,
        validators=[validate_product_template],
        help_text="Campos: {numero}, {producto}, {marca}, {cantidad_presentacion}, {unidad_precio}, {presentacion_adicional}, {precio}, {subtotal}. Cantidad/presentación se arma con la unidad y contenido registrado; la presentación adicional sólo aparece si aporta datos. Compatibilidad: {cantidad}, {unidad}, {descripcion} conservan su significado original. Conservá producto, precio, cantidad/unidad y subtotal.",
    )

    class Meta:
        verbose_name = "configuración comercial"
        verbose_name_plural = "configuración comercial"
        constraints = [models.CheckConstraint(condition=models.Q(pk=1), name="business_settings_single_row")]

    def clean(self):
        super().clean()
        if self.maps_url:
            url = urlsplit(self.maps_url)
            google = url.hostname in {"google.com", "www.google.com", "google.com.ar", "www.google.com.ar"} and url.path.startswith("/maps")
            shared = url.hostname == "maps.app.goo.gl" or (url.hostname == "goo.gl" and url.path.startswith("/maps/"))
            if url.scheme != "https" or url.username or url.password or not (google or shared or url.hostname == "maps.google.com"):
                raise ValidationError({"maps_url": "Ingresá un enlace HTTPS de Google Maps."})

    @property
    def location_url(self):
        if not self.address.strip():
            return ""
        return self.maps_url or "https://www.google.com/maps/search/?" + urlencode({"api": "1", "query": self.address.strip()})

    def __str__(self):
        return "Datos de Dulce y Salado"


class OpeningInterval(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Lunes"
        TUESDAY = 1, "Martes"
        WEDNESDAY = 2, "Miércoles"
        THURSDAY = 3, "Jueves"
        FRIDAY = 4, "Viernes"
        SATURDAY = 5, "Sábado"
        SUNDAY = 6, "Domingo"

    business = models.ForeignKey(BusinessSettings, on_delete=models.CASCADE, related_name="opening_intervals")
    weekday = models.PositiveSmallIntegerField("día", choices=Weekday.choices)
    opens_at = models.TimeField("apertura")
    closes_at = models.TimeField("cierre")

    class Meta:
        ordering = ["weekday", "opens_at", "pk"]
        verbose_name = "intervalo horario"
        verbose_name_plural = "intervalos horarios"
        constraints = [
            models.CheckConstraint(condition=models.Q(opens_at__lt=models.F("closes_at")), name="opening_before_closing"),
            models.CheckConstraint(condition=models.Q(weekday__gte=0, weekday__lte=6), name="opening_valid_weekday"),
        ]

    def clean(self):
        super().clean()
        if self.opens_at and self.closes_at and self.opens_at >= self.closes_at:
            raise ValidationError({"closes_at": "El cierre debe ser posterior a la apertura, dentro del mismo día."})

    def validate_constraints(self, exclude=None):
        super().validate_constraints(exclude)
        # Django excluye el FK inline; su formset valida todos los intervalos finales juntos.
        if exclude and "business" in exclude:
            return
        if self.business_id and self.weekday is not None and self.opens_at and self.closes_at:
            overlaps = type(self).objects.filter(
                business_id=self.business_id, weekday=self.weekday,
                opens_at__lt=self.closes_at, closes_at__gt=self.opens_at,
            ).exclude(pk=self.pk)
            if overlaps.exists():
                raise ValidationError("Los intervalos de un mismo día no pueden superponerse.")

    def __str__(self):
        return f"{self.get_weekday_display()}: {self.opens_at:%H:%M}–{self.closes_at:%H:%M}"


class Order(models.Model):
    """Solicitud inmutable; la secuencia PostgreSQL es el código comercial."""

    class Delivery(models.TextChoices):
        PICKUP = "pickup", "Retiro en el local"
        DELIVERY = "delivery", "Envío a domicilio"

    token = models.UUIDField(default=uuid4, unique=True, editable=False)
    confirmation_key = models.UUIDField(unique=True, editable=False)
    request_hash = models.CharField(max_length=64, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    full_name = models.CharField("nombre completo", max_length=120)
    delivery_mode = models.CharField("modalidad", max_length=8, choices=Delivery.choices)
    street = models.CharField("calle", max_length=160, blank=True)
    number = models.CharField("número", max_length=30, blank=True)
    city = models.CharField("ciudad", max_length=100, blank=True)
    items = models.JSONField("productos y precios originales", editable=False)
    total = models.DecimalField("total", max_digits=24, decimal_places=0, editable=False)
    detail_url = models.URLField(max_length=500, editable=False)
    message = models.TextField("mensaje preparado", editable=False)
    whatsapp_url = models.TextField("enlace preparado", editable=False)

    class Meta:
        ordering = ["-pk"]
        verbose_name = "solicitud de pedido"
        verbose_name_plural = "solicitudes de pedidos"

    @property
    def code(self):
        return f"DYS-{self.pk:06d}"

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Los pedidos preparados conservan su instantánea original.")
        return super().save(*args, **kwargs)
