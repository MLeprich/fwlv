"""
Richtet den Celery-Beat-Zeitplan für `idcards.expire_due_cards` ein.

Idempotent — kann beliebig oft aufgerufen werden:

    python manage.py setup_idcards_schedule

Standard: tägliche Ausführung um 03:00 Uhr Ortszeit.
Kann mit --hour / --minute überschrieben werden.
"""

from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask


TASK_NAME = 'idcards: Abgelaufene Karten markieren'
TASK_PATH = 'idcards.expire_due_cards'


class Command(BaseCommand):
    help = 'Legt den Celery-Beat-Eintrag für die tägliche EXPIRED-Markierung an.'

    def add_arguments(self, parser):
        parser.add_argument('--hour', type=int, default=3,
                            help='Stunde (0–23), Standard 3.')
        parser.add_argument('--minute', type=int, default=0,
                            help='Minute (0–59), Standard 0.')
        parser.add_argument('--remove', action='store_true',
                            help='Eintrag entfernen statt anlegen.')

    def handle(self, *args, **opts):
        if opts['remove']:
            deleted, _ = PeriodicTask.objects.filter(name=TASK_NAME).delete()
            self.stdout.write(self.style.SUCCESS(
                f'{deleted} Eintrag/Einträge entfernt.'
            ))
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
                    'Setzt aktive Dienstausweise mit überschrittenem '
                    'Gültig-bis-Datum auf EXPIRED.'
                ),
            },
        )
        verb = 'angelegt' if created else 'aktualisiert'
        self.stdout.write(self.style.SUCCESS(
            f'{verb}: {TASK_NAME} — {opts["hour"]:02d}:{opts["minute"]:02d}'
        ))
