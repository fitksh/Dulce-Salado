from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

from .models import BusinessSettings, Category, Product
from .whatsapp_templates import DEFAULT_PRODUCT_TEMPLATE


class SubtotalLabelMigrationTests(TransactionTestCase):
    def migrate_format(self, before, expected):
        old = [("catalog", "0006_whatsapp_message_templates")]
        current = [("catalog", "0007_whatsapp_subtotal_label")]
        MigrationExecutor(connection).migrate(old)
        try:
            apps = MigrationExecutor(connection).loader.project_state(old).apps
            business = apps.get_model("catalog", "BusinessSettings").objects.create(
                address="Dirección conservada", whatsapp_product_template=before)
            category = Category.objects.create(name="Existente", slug="existente")
            apps.get_model("catalog", "Product").objects.create(category_id=category.pk, name="Original", retail_price="10.25", image="products/original.webp")
            fields = [field.name for field in BusinessSettings._meta.fields if field.name != "whatsapp_product_template"]
            values = apps.get_model("catalog", "BusinessSettings").objects.values(*fields).get(pk=business.pk)
            products = list(Product.objects.values())
            MigrationExecutor(connection).migrate(current)
            self.assertEqual(BusinessSettings.objects.get().whatsapp_product_template, expected)
            self.assertEqual(BusinessSettings.objects.values(*fields).get(), values)
            self.assertEqual(list(Product.objects.values()), products)
        finally:
            MigrationExecutor(connection).migrate(MigrationExecutor(connection).loader.graph.leaf_nodes())

    def test_previous_default_gets_the_new_label_without_changing_other_data(self):
        self.migrate_format(DEFAULT_PRODUCT_TEMPLATE.replace("Subtotal:", "Subtotal estimado:"), DEFAULT_PRODUCT_TEMPLATE)

    def test_custom_format_only_changes_the_requested_label(self):
        self.migrate_format("🛍️ {producto}\n{cantidad} {unidad} {precio}\nSubtotal estimado: {subtotal}\nGracias!",
                            "🛍️ {producto}\n{cantidad} {unidad} {precio}\nSubtotal: {subtotal}\nGracias!")

    def test_custom_format_without_the_old_label_is_preserved(self):
        self.migrate_format("{producto} {cantidad} {unidad} × {precio} = {subtotal}",
                            "{producto} {cantidad} {unidad} × {precio} = {subtotal}")
