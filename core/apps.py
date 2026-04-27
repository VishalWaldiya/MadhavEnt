from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        import sys
        # Avoid running during management commands like makemigrations or migrate
        if 'makemigrations' in sys.argv or 'migrate' in sys.argv:
            return
            
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if not User.objects.filter(username='admin').exists():
                user = User.objects.create_superuser(username='admin', password='admin', email='admin@example.com')
                user.role = 'ADMIN'
                user.save()
                print("Successfully created default admin user (username: admin, password: admin)")
        except Exception:
            pass
