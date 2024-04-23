from celery import shared_task

from users.models import DemoWallet


@shared_task
def update_demo_wallet(wallet_id):
    wallet = DemoWallet.objects.get(id=wallet_id)
    wallet.balance = 100
    wallet.save()
    return 'Success'
