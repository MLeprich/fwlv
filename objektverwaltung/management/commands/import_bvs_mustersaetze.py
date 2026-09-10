"""
Management Command: Mustersätze der Brandverhütungsschau aus der PDF-Vorlage importieren

    python manage.py import_bvs_mustersaetze /tmp/bvs/Mustersaetze.pdf [--update] [--dry-run]

Ohne --update werden nur fehlende Kapitel und Mustersätze angelegt; bereits
vorhandene (und evtl. im System überarbeitete) Texte bleiben unverändert.
Nummern ohne Titel und Text (leere Platzhalter der Vorlage) werden übersprungen,
Mustersätze mit Titel aber ohne Text inaktiv angelegt.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from objektverwaltung.bvs_import import note_text, parse_pdf
from objektverwaltung.models import BVSPhrase, BVSPhraseCategory

EMPTY_NOTE = 'Text fehlt in der Vorlage.'


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

        update = options['update']
        stats = {'cat_new': 0, 'cat_upd': 0, 'new': 0, 'upd': 0, 'kept': 0, 'skipped': []}

        with transaction.atomic():
            categories = {}
            for cat in parsed.categories:
                values = {
                    'title': cat.title,
                    'parent': categories.get(cat.parent),
                    'sort_order': BVSPhraseCategory.sort_key_for(cat.number),
                }
                obj = BVSPhraseCategory.objects.filter(number=cat.number).first()
                if obj is None:
                    obj = BVSPhraseCategory.objects.create(number=cat.number, **values)
                    stats['cat_new'] += 1
                elif update:
                    for key, value in values.items():
                        setattr(obj, key, value)
                    obj.save()
                    stats['cat_upd'] += 1
                categories[cat.number] = obj
                if cat.notes:
                    self.stdout.write(self.style.WARNING(f'  Hinweis zu {cat.number} {cat.title}: {note_text(cat.notes)}'))

            for phrase in parsed.phrases:
                if not phrase.title and not phrase.text:
                    stats['skipped'].append(phrase.code)
                    continue
                notes = [note_text(phrase.notes)] if phrase.notes else []
                if not phrase.text:
                    notes.append(EMPTY_NOTE)
                values = {
                    'category': categories[phrase.category],
                    'title': phrase.title or f'Mustersatz {phrase.code}',
                    'text': phrase.text,
                    'review_note': '\n'.join(notes),
                    'is_active': bool(phrase.text),
                    'sort_order': int(phrase.code),
                }
                obj = BVSPhrase.objects.filter(code=phrase.code).first()
                if obj is None:
                    BVSPhrase.objects.create(code=phrase.code, **values)
                    stats['new'] += 1
                elif update:
                    for key, value in values.items():
                        setattr(obj, key, value)
                    obj.save()
                    stats['upd'] += 1
                else:
                    stats['kept'] += 1

            if options['dry_run']:
                transaction.set_rollback(True)

        prefix = '[DRY RUN] ' if options['dry_run'] else ''
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}Kapitel/Abschnitte: {stats['cat_new']} neu, {stats['cat_upd']} aktualisiert\n"
            f"{prefix}Mustersätze: {stats['new']} neu, {stats['upd']} aktualisiert, "
            f"{stats['kept']} unverändert gelassen"
        ))
        if stats['skipped']:
            self.stdout.write(f"Leere Nummern übersprungen: {', '.join(stats['skipped'])}")
        flagged = BVSPhrase.objects.exclude(review_note='').count() if not options['dry_run'] else None
        if flagged:
            self.stdout.write(self.style.WARNING(
                f'{flagged} Mustersätze haben einen Prüfhinweis (Randkommentare/fehlender Text) – '
                'bitte unter „Mustersätze“ durchsehen.'
            ))
