"""
Markiert abgelaufene aktive Dienstausweise als EXPIRED.

Anwendung (z.B. via Cron, einmal pro Tag):
    python manage.py expire_idcards
"""

from django.core.management.base import BaseCommand

from idcards.services import expire_due_cards


class Command(BaseCommand):
    help = 'Setzt alle aktiven Dienstausweise mit überschrittenem valid_until auf EXPIRED.'

    def handle(self, *args, **options):
        count = expire_due_cards()
        self.stdout.write(self.style.SUCCESS(
            f'{count} Karte(n) auf EXPIRED gesetzt.'
        ))
