"""
Management Command: Mustersätze der Brandverhütungsschau aus der PDF-Vorlage importieren

    python manage.py import_bvs_mustersaetze /tmp/bvs/Mustersaetze.pdf [--update] [--dry-run]

Dasselbe geht in der Oberfläche unter Brandverhütungsschau → Mustersätze → „PDF importieren“.
Ohne --update werden nur fehlende Kapitel und Mustersätze angelegt; bereits
vorhandene (und evtl. im System überarbeitete) Texte bleiben unverändert.
"""

from django.core.management.base import BaseCommand, CommandError

from objektverwaltung.bvs_import import import_phrases, parse_pdf
from objektverwaltung.models import BVSPhrase


class Command(BaseCommand):
    help = 'Importiert die Mustersätze der Brandverhütungsschau aus der PDF-Vorlage'

    def add_arguments(self, parser):
        parser.add_argument('pdf', help='Pfad zur PDF-Datei „Mustersätze für Stellungnahmen“')
        parser.add_argument('--update', action='store_true',
                            help='Vorhandene Kapitel und Mustersätze mit dem Stand der PDF überschreiben')
        parser.add_argument('--dry-run', action='store_true', help='Nur anzeigen, nichts speichern')

    def handle(self, *args, **options):
        try:
            parsed = parse_pdf(options['pdf'])
        except (OSError, RuntimeError) as exc:
            raise CommandError(f'PDF konnte nicht gelesen werden: {exc}')
        if not parsed.phrases:
            raise CommandError('In der PDF wurden keine Mustersätze gefunden.')

        stats = import_phrases(parsed, update=options['update'], dry_run=options['dry_run'])
        for note in stats.category_notes:
            self.stdout.write(self.style.WARNING(f'  Hinweis zu {note}'))
        prefix = '[DRY RUN] ' if stats.dry_run else ''
        self.stdout.write(self.style.SUCCESS(prefix + stats.summary))
        flagged = BVSPhrase.objects.exclude(review_note='').count() if not stats.dry_run else 0
        if flagged:
            self.stdout.write(self.style.WARNING(
                f'{flagged} Mustersätze haben einen Prüfhinweis (Randkommentare/fehlender Text) – '
                'bitte unter „Mustersätze“ durchsehen.'
            ))
