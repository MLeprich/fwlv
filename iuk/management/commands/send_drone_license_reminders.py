"""
Erinnert an ablaufende Drohnenführerscheine.

    python manage.py send_drone_license_reminders
    python manage.py send_drone_license_reminders --days 60 --dry-run

Erzeugt ausschließlich In-App-Benachrichtigungen (Glocken-Symbol), keine E-Mails.
Pro Führerschein wird höchstens alle 30 Tage erinnert – der Befehl kann also
gefahrlos täglich laufen (Cron oder Celery-Beat).
"""

from django.core.management.base import BaseCommand

from iuk.models import WARNING_DAYS
from iuk.services import send_license_reminders


class Command(BaseCommand):
    help = 'Erinnert an ablaufende Drohnenführerscheine (nur In-App-Benachrichtigung).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', type=int, default=WARNING_DAYS,
            help=f'Vorlauf in Tagen (Standard: {WARNING_DAYS}).',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Nur anzeigen, wofür erinnert würde.',
        )

    def handle(self, *args, **options):
        result = send_license_reminders(
            lead_days=options['days'],
            dry_run=options['dry_run'],
        )

        if result['dry_run']:
            self.stdout.write(self.style.NOTICE('[DRY RUN] Es wurde nichts gespeichert.'))

        self.stdout.write(
            f'Geprüft: {result["checked"]} Führerschein(e) mit Ablauf in '
            f'{result["lead_days"]} Tagen oder früher'
        )
        self.stdout.write(
            f'Erinnert: {result["licenses_notified"]} Führerschein(e), '
            f'{result["notifications"]} Benachrichtigung(en)'
        )
        if result['skipped_recent']:
            self.stdout.write(
                f'Übersprungen (kürzlich erinnert): {result["skipped_recent"]}'
            )
        if result['skipped_no_recipient']:
            self.stdout.write(self.style.WARNING(
                f'Ohne Empfänger: {result["skipped_no_recipient"]} – Benutzerkonto '
                f'der Person fehlt und keine Modulverantwortlichen hinterlegt.'
            ))
        self.stdout.write(self.style.SUCCESS('✓ Fertig'))
