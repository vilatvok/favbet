from django.dispatch import receiver
from django.db.models.signals import post_save

from users.models import User, DemoWallet


@receiver(post_save, sender=User)
def create_demo_wallet(sender, instance, created, **kwargs):
    if created:
        DemoWallet.objects.create(user=instance)
