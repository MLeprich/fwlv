"""
Richtet den Celery-Beat-Zeitplan für `iuk.drone_license_reminders` ein.

Idempotent – kann beliebig oft aufgerufen werden:

    python manage.py setup_iuk_schedule

Standard: tägliche Ausführung um 06:00 Uhr Ortszeit.
"""

from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask

TASK_NAME = 'IUK: Erinnerung Drohnenführerscheine'
TASK_PATH = 'iuk.drone_license_reminders'


class Command(BaseCommand):
    help = 'Legt den Celery-Beat-Eintrag für die täglichen Führerschein-Erinnerungen an.'

    def add_arguments(self, parser):
        parser.add_argument('--hour', type=int, default=6, help='Stunde (0–23), Standard 6.')
        parser.add_argument('--minute', type=int, default=0, help='Minute (0–59), Standard 0.')
        parser.add_argument('--remove', action='store_true', help='Eintrag entfernen statt anlegen.')

    def handle(self, *args, **opts):
        if opts['remove']:
            deleted, _ = PeriodicTask.objects.filter(name=TASK_NAME).delete()
            self.stdout.write(self.style.SUCCESS(f'{deleted} Eintrag/Einträge entfernt.'))
            return

        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=str(opts['minute']),
            hour=str(opts['hour']),
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )

        task, created = PeriodicTask.objects.update_or_create(
            name=TASK_NAME,
            defaults={
                'crontab': schedule,
                'task': TASK_PATH,
                'enabled': True,
                'description': (
                    'Benachrichtigt Fernpiloten und Modulverantwortliche über '
                    'ablaufende oder abgelaufene Drohnenführerscheine.'
                ),
            },
        )
        verb = 'angelegt' if created else 'aktualisiert'
        self.stdout.write(self.style.SUCCESS(
            f'{verb}: {TASK_NAME} — {opts["hour"]:02d}:{opts["minute"]:02d}'
        ))
