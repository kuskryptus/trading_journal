import shlex
import subprocess

from django.core.management.base import BaseCommand
from django.utils import autoreload
from trading_signals.tasks import notification_pair


class Command(BaseCommand):
    help = 'Adds a periodic task for checking signals'

    def handle(self, *args, **options):
        celery_path = r'C:\Users\Kristian\Desktop\forex_journal_django\venv\Scripts\celery.exe'
        cmd = f'{celery_path} -f "forex_journal worker"'
        subprocess.call(shlex.split(cmd))
        cmd = f'{celery_path} -A forex_journal worker -l INFO --pool=threads -Q notification-pair --concurrency=1'
        subprocess.call(shlex.split(cmd))
        notification_pair.apply_async()
