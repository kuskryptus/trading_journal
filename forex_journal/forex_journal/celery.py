import logging
import os

import psutil

from celery import Celery

# set the default Django settings module for the celery.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forex_journal.settings')


app = Celery('forex_journal')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.task_routes = {'forex_journal.trading_signals.tasks.notification_pair': {'queue': 'notification-pair'}}
app.conf.task_routes = {'forex_journal.trading_signals.tasks.notification_indicator': {'queue': 'notification-indicator'}}
app.conf.task_routes = {'forex_journal.trading_signals.tasks.process_price_for_pair': {'queue': 'notification-indicator'}}
app.autodiscover_tasks()


""" app.conf.beat_schedule = {
    "check_for_sygnal": {
        "task" : "trading_signals.tasks.notification_indicator",
        "schedule" : timedelta(seconds=30)
    }
} """


def stop_specific_celery_worker(queue_name):
    # Iterating through all processes and request the celery workers handling the specified queue to terminate
    for proc in psutil.process_iter(['pid', 'cmdline']):
        if 'celery' in proc.info['cmdline'] and queue_name in proc.info['cmdline']:
            try:
                p = psutil.Process(proc.info['pid'])
                p.terminate()
                print(f"Requested Celery worker with PID {proc.info['pid']} handling queue '{queue_name}' to stop")
            except psutil.NoSuchProcess:
                print(f"Celery worker with PID {proc.info['pid']} handling queue '{queue_name}' not found")


log = logging.getLogger(__name__)


logging.basicConfig(
    format='%(asctime)s [%(levelname)s] - %(message)s',
    level=logging.INFO  
)

log = logging.getLogger('celery.task')