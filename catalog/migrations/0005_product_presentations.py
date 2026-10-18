from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


def fixed_increment(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    Product.objects.using(schema_editor.connection.alias).exclude(quantity_step=1).update(quantity_step=1)


class Migration(migrations.Migration):
    dependencies = [("catalog", "0004_opening_hours")]
    operations = [
        migrations.RemoveConstraint(model_name="product", name="product_positive_step"),
        migrations.RemoveConstraint(model_name="product", name="product_valid_unit"),
        # Una copia previa conserva los incrementos anteriores: revertir el
        # esquema no restaura esos valores. No convertir unidades, importes, imágenes ni presentaciones.
        migrations.RunPython(fixed_increment, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="product", name="quantity_step",
            field=models.DecimalField(verbose_name="incremento de cantidad", max_digits=9,
                                      decimal_places=2, default=Decimal("1"), editable=False,
                                      validators=[MinValueValidator(Decimal("1")), MaxValueValidator(Decimal("1"))],
                                      help_text="Siempre una presentación por vez."),
        ),
        migrations.AlterField(
            model_name="product", name="sale_unit",
            field=models.CharField(verbose_name="unidad de venta", max_length=10, default="kg",
                                   choices=[("100 gr", "100 gr"), ("kg", "kg"), ("caja", "caja"),
                                            ("pack", "pack"), ("paquete", "paquete"), ("bolsa", "bolsa")]),
        ),
        migrations.AddConstraint(model_name="product", constraint=models.CheckConstraint(
            condition=models.Q(quantity_step=1), name="product_fixed_step")),
        migrations.AddConstraint(model_name="product", constraint=models.CheckConstraint(
            condition=models.Q(sale_unit__in=["100 gr", "kg", "caja", "pack", "paquete", "bolsa", "unidad"]),
            name="product_valid_unit")),
    ]
