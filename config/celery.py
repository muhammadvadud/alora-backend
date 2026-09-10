import os

from celery import Celery
from celery.schedules import crontab

# Standart sozlamalar
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

app = Celery('alora')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Ishlab chiqarish muhiti uchun ishonchli task bajarilishi sozlamalari.
app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    task_time_limit=300,
    task_soft_time_limit=270,
    result_expires=86_400,
)

# Navbatlar sozlamalari
app.conf.task_routes = {
    'apps.usage.tasks.*': {'queue': 'usage'},
    'apps.chat.tasks.*': {'queue': 'usage'},
    'apps.catalog.tasks.compress_image_task': {'queue': 'heavy'},
    'apps.usage.tasks.daily_usage_rollup': {'queue': 'heavy'},
    'apps.chat.tasks.archive_old_conversations': {'queue': 'heavy'},
}

# Standart navbat
app.conf.task_default_queue = 'default'

# Beat jadvali
app.conf.beat_schedule = {
    'daily_usage_rollup': {
        'task': 'apps.usage.tasks.daily_usage_rollup',
        'schedule': crontab(minute=5, hour=0), # Har kuni 00:05
    },
    'archive_old_conversations': {
        'task': 'apps.chat.tasks.archive_old_conversations',
        'schedule': crontab(minute=0, hour=3, day_of_week='sunday'), # Haftalik yakshanba tunda
    },
    'check_limits_and_notify': {
        'task': 'apps.usage.tasks.check_limits_and_notify',
        'schedule': crontab(minute=0), # Har soatda
    },
    'stock_low_alert': {
        'task': 'apps.catalog.tasks.stock_low_alert',
        'schedule': crontab(minute=30, hour=8), # Har kuni 08:30
    }
}
