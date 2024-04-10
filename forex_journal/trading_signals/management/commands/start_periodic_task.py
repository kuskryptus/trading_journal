from django.core.management.base import BaseCommand
from django_celery_beat.models import IntervalSchedule, PeriodicTask
from trading_signals.tasks import notification_indicator

class Command(BaseCommand):
    help = 'Enables and updates a periodic task for checking signals'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int)

    def handle(self, *args, **options):
        user_id = options['user_id']
        interval, _ = IntervalSchedule.objects.get_or_create(every=30, period=IntervalSchedule.SECONDS)

        existing_task = PeriodicTask.objects.filter(name="check_for_signal").first()
        if existing_task:
            # Perform the update
            existing_task.interval = interval 
            existing_task.task = "trading_signals.tasks.notification_indicator"
            existing_task.args = '[]'
            existing_task.kwargs = f'{{"user_id": {user_id}}}'  
            existing_task.enabled = True 
            existing_task.routing_key = 'notification_indicator'  
            existing_task.save()
            self.stdout.write(self.style.SUCCESS('Successfully updated periodic task'))
        else:
            # Create a new task if it doesn't exist
            task = PeriodicTask.objects.create(
                name="check_for_sygnal",
                task="trading_signals.tasks.notification_indicator",
                interval=interval,
                args='[]',
                kwargs=f'{{"user_id": {user_id}}}',
                enabled=True,
                routing_key='notification_indicator'
            )
            self.stdout.write(self.style.SUCCESS('Successfully added periodic task'))
