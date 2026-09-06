import os
from django.core.management import call_command
from django.contrib.staticfiles.management.commands.runserver import Command as StaticfilesRunserverCommand

class Command(StaticfilesRunserverCommand):
    help = 'Starts the Django development server after running makemigrations and migrate.'

    def handle(self, *args, **options):
        # Prevent executing twice during statreload
        if os.environ.get('RUN_MAIN') != 'true':
            self.stdout.write(self.style.MIGRATE_HEADING("Running automatic database migrations (makemigrations & migrate)..."))
            try:
                call_command('makemigrations')
                call_command('migrate')
                self.stdout.write(self.style.SUCCESS("Database migrations complete!"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Automatic migration warning: {e}"))

        super().handle(*args, **options)
