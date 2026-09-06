from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates or updates the default admin superuser (admin / Madhav@2027).'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Creating default admin user..."))

        # Superuser Creation
        admin_user = User.all_objects.filter(username='admin').first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                username='admin',
                password='Madhav@2027',
                first_name='Administrator',
                last_name='Admin',
                role='ADMIN',
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(self.style.SUCCESS("Superuser 'admin' created successfully with password 'Madhav@2027'."))
        else:
            admin_user.set_password('Madhav@2027')
            admin_user.first_name = 'Administrator'
            admin_user.last_name = 'Admin'
            admin_user.role = 'ADMIN'
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.is_deleted = False
            admin_user.is_active = True
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Superuser 'admin' updated successfully with password '********'."))

        self.stdout.write(self.style.SUCCESS("Default admin user setup complete!"))
