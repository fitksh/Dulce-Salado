from decimal import Decimal
from urllib.parse import urlencode, urlsplit

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction

from .images import optimize_product_image, product_image_path, validate_product_image


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
        KG = "kg", "kg"
        UNIT = "unidad", "unidad"
        PACKAGE = "paquete", "paquete"

    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name="categoría")
    name = models.CharField("nombre", max_length=180)
    brand = models.CharField("marca", max_length=100, blank=True)
    description = models.TextField("descripción", blank=True)
    sale_unit = models.CharField("unidad de venta", max_length=10, choices=SaleUnit.choices, default=SaleUnit.UNIT)
    quantity_step = models.DecimalField(
        "incremento de cantidad", max_digits=9, decimal_places=2, default=Decimal("1"),
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Cantidad positiva. En unidad/paquete debe ser entera. Inicial: 0,1 kg o 1 unidad/paquete.",
    )
    retail_price = models.DecimalField(
        "precio minorista (ARS)", max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    wholesale_price = models.DecimalField(
        "precio mayorista (ARS)", max_digits=12, decimal_places=2, blank=True, null=True,
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
            models.CheckConstraint(condition=models.Q(quantity_step__gt=0), name="product_positive_step"),
            models.CheckConstraint(condition=models.Q(retail_price__gte=0), name="product_nonnegative_retail"),
            models.CheckConstraint(
                condition=models.Q(wholesale_price__isnull=True) | models.Q(wholesale_price__gte=0),
                name="product_nonnegative_wholesale",
            ),
            models.CheckConstraint(condition=models.Q(sale_unit__in=["kg", "unidad", "paquete"]), name="product_valid_unit"),
        ]

    def clean(self):
        super().clean()
        if self.quantity_step is not None and self.sale_unit != self.SaleUnit.KG:
            if self.quantity_step != self.quantity_step.to_integral_value():
                raise ValidationError({"quantity_step": "Unidad y paquete requieren incrementos enteros."})

    def __str__(self):
        return f"{self.name} — {self.brand}" if self.brand else self.name

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
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
