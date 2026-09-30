"""
Kartenkacheln für den Offline-Betrieb herunterladen (auf einer Maschine MIT Internet).

    python manage.py tiles_download --bbox 51.44,6.78,51.56,6.95 --zoom 11-17 [--zip stadt-kacheln.zip]

Ohne --bbox/--zoom werden Stadtgebiet und Zoomstufen aus den Karteneinstellungen genutzt.
Vorhandene Kacheln werden übersprungen, mit --dry-run wird nur gezählt.

Standardquelle ist TopPlusOpen des Bundesamts für Kartographie und Geodäsie (offene
Daten, Lizenz dl-de/by-2-0, Quellenangabe „© GeoBasis-DE / BKG <Jahr>“). Alternativen per --url:
  Luftbild NRW (Geobasis NRW, dl-de/zero-2-0):
    --url "https://www.wmts.nrw.de/geobasis/wmts_nw_dop/tiles/nw_dop/EPSG_3857_16/{z}/{y}/{x}"
Der öffentliche OpenStreetMap-Kachelserver ist für Massen-Downloads gesperrt (liefert
Sperrbilder) und deshalb keine geeignete Quelle.
"""
import time
import urllib.request
import zipfile
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from einsatzvorbereitung import tiles
from einsatzvorbereitung.models import MapConfig

USER_AGENT = 'FLVS-Einsatzvorbereitung/1.0 (Offline-Karte Feuerwehr; Kontakt siehe Betreiber)'
#: TopPlusOpen (BKG) – offene Web-Karte für ganz Deutschland, Kachelschema z/y/x
DEFAULT_URL = 'https://sgx.geodatenzentrum.de/wmts_topplus_open/tile/1.0.0/web/default/WEBMERCATOR/{z}/{y}/{x}.png'


class Command(BaseCommand):
    help = 'Kartenkacheln für den Offline-Betrieb herunterladen'

    def add_arguments(self, parser):
        parser.add_argument('--url', default=DEFAULT_URL, help='Kachel-URL-Vorlage mit {z}, {x}, {y}')
        parser.add_argument('--bbox', help='Süd,West,Nord,Ost (Standard: Karteneinstellungen)')
        parser.add_argument('--zoom', default=None, help='z.B. 11-17 (Standard: Karteneinstellungen)')
        parser.add_argument('--out', default=None, help='Zielordner (Standard: MEDIA_ROOT/tiles)')
        parser.add_argument('--zip', default=None, help='Zusätzlich als ZIP verpacken (für tiles_import)')
        parser.add_argument('--delay', type=float, default=0.2, help='Pause zwischen Anfragen in Sekunden')
        parser.add_argument('--overwrite', action='store_true')
        parser.add_argument('--dry-run', action='store_true', help='Nur zählen, nichts laden')

    def handle(self, *args, **options):
        config = MapConfig.load()
        bbox_text = options['bbox'] or config.bbox
        if not bbox_text:
            raise CommandError('Kein Gebiet: --bbox Süd,West,Nord,Ost angeben oder in den Karteneinstellungen hinterlegen.')
        try:
            bbox = [float(p) for p in bbox_text.split(',')]
            assert len(bbox) == 4 and bbox[0] < bbox[2] and bbox[1] < bbox[3]
        except (ValueError, AssertionError):
            raise CommandError('Ungültiges Gebiet. Format: Süd,West,Nord,Ost – z.B. 51.44,6.78,51.56,6.95')
        zoom_text = options['zoom'] or f'{config.min_zoom}-{config.max_zoom}'
        try:
            lo, hi = (int(p) for p in zoom_text.split('-')) if '-' in zoom_text else (int(zoom_text), int(zoom_text))
            assert 0 <= lo <= hi <= 19
        except (ValueError, AssertionError):
            raise CommandError('Ungültige Zoomstufen, z.B. 11-17')
        zooms = range(lo, hi + 1)
        out = Path(options['out']) if options['out'] else tiles.tiles_dir()
        total = tiles.count_tiles(bbox, zooms)
        self.stdout.write(f'Gebiet {bbox}, Zoom {lo}-{hi}: {total} Kacheln → {out}')
        if total > 60000:
            self.stdout.write(self.style.WARNING(
                'Das sind sehr viele Kacheln – Gebiet verkleinern oder maximalen Zoom senken.'))
        if options['dry_run']:
            return

        done = skipped = failed = 0
        for z in zooms:
            x1, x2, y1, y2 = tiles.tile_range(bbox, z)
            for x in range(x1, x2 + 1):
                for y in range(y1, y2 + 1):
                    path = out / str(z) / str(x) / f'{y}.png'
                    if path.is_file() and not options['overwrite']:
                        skipped += 1
                        continue
                    url = options['url'].format(z=z, x=x, y=y)
                    try:
                        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
                        with urllib.request.urlopen(req, timeout=30) as resp:
                            content_type = resp.headers.get('Content-Type', '')
                            data = resp.read()
                        # Nur echte Bilder speichern – Sperr-/Fehlerseiten (z.B. „Access blocked“) verwerfen
                        if not content_type.startswith('image/') or not data[:4] in (b'\x89PNG', b'\xff\xd8\xff\xe0', b'\xff\xd8\xff\xe1', b'\xff\xd8\xff\xdb'):
                            raise ValueError(f'keine Bildkachel ({content_type or "unbekannter Typ"})')
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(data)
                        done += 1
                    except Exception as exc:  # noqa: BLE001
                        failed += 1
                        self.stderr.write(f'  ✗ {url}: {exc}')
                        if failed >= 20 and done == 0:
                            raise CommandError('Die ersten 20 Kacheln sind fehlgeschlagen – Quelle/URL-Vorlage prüfen.')
                    if options['delay']:
                        time.sleep(options['delay'])
                    if (done + skipped + failed) % 200 == 0:
                        self.stdout.write(f'  … {done + skipped + failed}/{total}')
        self.stdout.write(self.style.SUCCESS(f'✓ {done} geladen, {skipped} vorhanden, {failed} fehlgeschlagen'))

        if options['zip']:
            zip_path = Path(options['zip'])
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as zf:
                for f in out.rglob('*.png'):
                    zf.write(f, f.relative_to(out))
            self.stdout.write(self.style.SUCCESS(f'✓ ZIP geschrieben: {zip_path} – auf der Zielmaschine: '
                                                 f'manage.py tiles_import {zip_path.name}'))
