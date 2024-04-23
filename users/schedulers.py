import json

from datetime import date, timedelta

from django_celery_beat.schedulers import CrontabSchedule, PeriodicTask


def schedule_demo_wallet(wallet_id):
    date_ = date.today() + timedelta(days=3)
    crontab, _ = CrontabSchedule.objects.get_or_create(
        day_of_month=date_.day,
        month_of_year=date_.month,
    )
    PeriodicTask.objects.create(
        crontab=crontab,
        name=f'update-demo-wallet-{wallet_id}',
        task='users.tasks.update_demo_wallet',
        args=json.dumps([wallet_id]),
    )
