from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Product


@receiver(post_delete, sender=Product)
def delete_product_image(sender, instance, **kwargs):
    if instance.image:
        name, storage = instance.image.name, instance.image.storage
        transaction.on_commit(lambda: storage.delete(name))
