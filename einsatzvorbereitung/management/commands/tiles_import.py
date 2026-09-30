"""
Kachel-ZIP (aus tiles_download --zip) auf der Offline-Maschine einspielen.

    python manage.py tiles_import stadt-kacheln.zip [--out ORDNER] [--replace]
"""
import shutil
import zipfile
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
        if options['replace'] and out.is_dir():
            shutil.rmtree(out)
        out.mkdir(parents=True, exist_ok=True)
        count = 0
        with zipfile.ZipFile(src) as zf:
            for member in zf.namelist():
                parts = Path(member).parts
                # nur z/x/y.png – alles andere (Pfade nach oben, Fremddateien) ignorieren
                if len(parts) != 3 or not parts[0].isdigit() or not parts[1].isdigit() or not parts[2].endswith('.png'):
                    continue
                target = out / parts[0] / parts[1] / parts[2]
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as f, open(target, 'wb') as t:
                    shutil.copyfileobj(f, t)
                count += 1
        status = tiles.tiles_status()
        self.stdout.write(self.style.SUCCESS(
            f'✓ {count} Kacheln eingespielt → {out} (gesamt {status["total"]} Kacheln, {status["size_mb"]} MB)'))
