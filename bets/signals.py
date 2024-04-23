from django.dispatch import receiver
from django.db.models import F
from django.db.models.signals import post_save
from django.core.exceptions import ValidationError

from bets.tasks import send_bet_letter
from bets.models import Bet


@receiver(post_save, sender=Bet)
def created_bet(sender, instance, created, **kwargs):
    if created:
        wallet = instance.user.demo_wallet
        if wallet.is_active:
            amount = instance.amount
            if wallet.balance < amount:
                raise ValidationError('Insufficient funds')
            wallet.balance = F('balance') - amount
            wallet.save()
        send_bet_letter.delay(instance.id)
