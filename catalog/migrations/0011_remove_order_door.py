from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("catalog", "0010_order")]

    operations = [migrations.RemoveField(model_name="order", name="door")]
