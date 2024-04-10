from django.core.management.base import BaseCommand
from journal.models import Journal, Asset, migrations
from journal.models import Journal

class Command(BaseCommand):
    help = "Fixes the journal_pairs foreign key issue after migration."

    def handle(self, *args, **kwargs):
        
    

        class Migration(migrations.Migration):
            journal = Journal()
            dependencies = [
                ('journal', '0016_previous_migration'), # Adjust this!
            ]

            operations = [
                migrations.RunPython(journal.fix_journal_pairs), 
            ]