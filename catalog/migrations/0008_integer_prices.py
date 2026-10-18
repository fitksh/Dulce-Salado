from decimal import Decimal, ROUND_DOWN

import django.core.validators
from django.db import migrations, models


def discard_cents(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    products = Product.objects.using(schema_editor.connection.alias)
    for product in products.only("pk", "retail_price", "wholesale_price").iterator():
        values = {name: getattr(product, name).quantize(Decimal("1"), rounding=ROUND_DOWN)
                  for name in ("retail_price", "wholesale_price") if getattr(product, name) is not None}
        # QuerySet.update conserva fecha de edición, fotos y demás datos.
        products.filter(pk=product.pk).update(**values)


class Migration(migrations.Migration):
    dependencies = [("catalog", "0007_whatsapp_subtotal_label")]
    operations = [
        # Truncar ANTES de cambiar la precisión: PostgreSQL redondearía al alterar numeric.
        # Revertir el esquema no recupera los centavos; se requiere el respaldo previo.
        migrations.RunPython(discard_cents, migrations.RunPython.noop),
        migrations.AlterField(model_name="product", name="retail_price",
            field=models.DecimalField(decimal_places=0, max_digits=12,
                validators=[django.core.validators.MinValueValidator(Decimal("0"))], verbose_name="precio minorista (ARS)")),
        migrations.AlterField(model_name="product", name="wholesale_price",
            field=models.DecimalField(blank=True, null=True, decimal_places=0, max_digits=12,
                validators=[django.core.validators.MinValueValidator(Decimal("0"))], verbose_name="precio mayorista (ARS)")),
    ]
