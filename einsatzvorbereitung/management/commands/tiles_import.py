"""
Kachel-ZIP (aus tiles_download --zip) auf der Offline-Maschine einspielen.

    python manage.py tiles_import stadt-kacheln.zip [--out ORDNER] [--replace]
"""
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from einsatzvorbereitung import tiles


class Command(BaseCommand):
    help = 'Kachel-ZIP in den Offline-Kachelordner entpacken'

    def add_arguments(self, parser):
        parser.add_argument('zipfile')
        parser.add_argument('--out', default=None, help='Zielordner (Standard: MEDIA_ROOT/tiles)')
        parser.add_argument('--replace', action='store_true', help='Vorhandene Kacheln vorher löschen')

    def handle(self, *args, **options):
        src = Path(options['zipfile'])
        if not src.is_file():
            raise CommandError(f'Datei nicht gefunden: {src}')
        out = Path(options['out']) if options['out'] else tiles.tiles_dir()
        with open(src, 'rb') as f:
            count, skipped = tiles.import_zip(f, out=out, replace=options['replace'])
        status = tiles.tiles_status()
        self.stdout.write(self.style.SUCCESS(
            f'✓ {count} Kacheln eingespielt → {out} (gesamt {status["total"]} Kacheln, {status["size_mb"]} MB)'))
