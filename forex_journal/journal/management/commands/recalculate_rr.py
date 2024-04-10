from django.core.management.base import BaseCommand
from journal.models import Asset

class Command(BaseCommand):
    help = 'Recalculate R:R values for all Asset records'

    def handle(self, *args, **options):
        assets = Asset.objects.all()

        for asset in assets:
            asset.save()

        self.stdout.write(self.style.SUCCESS('Successfully recalculated R:R values for all Asset records'))