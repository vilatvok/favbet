import os

from django.conf import settings

from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'favbet.settings')

app = Celery('favbet')
app.config_from_object('django.conf:settings')
app.conf.broker_url = settings.CELERY_BROKER
app.conf.beat_scheduler = settings.CELERY_BEAT_SCHEDULER
app.conf.broker_connection_retry_on_startup = True
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'set-matches': {
        'task': 'bets.tasks.set_matches',
        'schedule': crontab(hour=0, minute=0),
    },
}
