#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_project.settings')
    try:
        from django.core.management import execute_from_command_line, call_command
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    if len(sys.argv) > 1 and sys.argv[1] == 'runserver' and os.environ.get('RUN_MAIN') != 'true':
        import django
        django.setup()
        print("Running automatic database migrations (makemigrations & migrate)...")
        try:
            call_command('makemigrations')
            call_command('migrate')
            print("Database migrations complete!")
        except Exception as e:
            print(f"Automatic migration warning: {e}")

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
