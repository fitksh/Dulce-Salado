import catalog.whatsapp_templates
from django.db import migrations, models

OLD_WARNING = "Los precios mostrados son estimados y pueden cambiar. La disponibilidad y la aplicación del precio mayorista están sujetas a confirmación del comercio por WhatsApp."
OLD_MESSAGE = "Hola! Quisiera realizar el siguiente pedido 🛍️:\n\n{productos}\n\n```💰 Total:       {total}```\n\n" + OLD_WARNING
OLD_PRODUCT = "{numero}. {producto}\n• Presentación: {descripcion}\n• Marca: {marca}\n• Precio minorista: {precio}/{unidad}\n• Cantidad: {cantidad} {unidad}\n• Subtotal: {subtotal}\n\n────────────"
NEW_MESSAGE = "Hola! Quisiera realizar el siguiente pedido 🛍️:\n\n{productos}\n\n────────────\n\n*💰 Total: {total}*\n\n📌 Los precios y la disponibilidad de los productos se confirmarán al procesar el pedido."
NEW_PRODUCT = "*{numero}. {producto}*\nMarca: {marca}\nCantidad: {cantidad_presentacion}\nPresentación: {presentacion_adicional}\nPrecio: {precio} por {unidad_precio}\n*Subtotal: {subtotal}*"


def update_defaults(apps, schema_editor):
    settings = apps.get_model("catalog", "BusinessSettings").objects.using(schema_editor.connection.alias)
    settings.filter(whatsapp_message_template=OLD_MESSAGE).update(whatsapp_message_template=NEW_MESSAGE)
    for before in (OLD_PRODUCT, OLD_PRODUCT.replace("Subtotal:", "Subtotal estimado:")):
        settings.filter(whatsapp_product_template=before).update(whatsapp_product_template=NEW_PRODUCT)


class Migration(migrations.Migration):
    dependencies = [("catalog", "0008_integer_prices")]
    operations = [
        migrations.RunPython(update_defaults, migrations.RunPython.noop),
        migrations.AlterField(model_name="businesssettings", name="whatsapp_message_template",
            field=models.TextField(default=NEW_MESSAGE, max_length=5000,
                validators=[catalog.whatsapp_templates.validate_message_template], verbose_name="mensaje general de WhatsApp",
                help_text="Cambiá frases, emojis y orden. Conservá {productos} para el listado y {total} para el importe calculado. Los campos se completan automáticamente con el carrito.")),
        migrations.AlterField(model_name="businesssettings", name="whatsapp_product_template",
            field=models.TextField(default=NEW_PRODUCT, max_length=3000,
                validators=[catalog.whatsapp_templates.validate_product_template], verbose_name="formato de cada producto",
                help_text="Campos: {numero}, {producto}, {marca}, {cantidad_presentacion}, {unidad_precio}, {presentacion_adicional}, {precio}, {subtotal}. Cantidad/presentación se arma con la unidad y contenido registrado; la presentación adicional sólo aparece si aporta datos. Compatibilidad: {cantidad}, {unidad}, {descripcion} conservan su significado original. Conservá producto, precio, cantidad/unidad y subtotal.")),
    ]
