from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator


class User(AbstractUser):
    email = models.EmailField(unique=True)


class DemoWallet(models.Model):
    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE,
        related_name='demo_wallet',
    )
    balance = models.FloatField(default=100, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username
