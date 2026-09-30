"""
Offline-Kartenkacheln

Die Karte lädt Kacheln ausschließlich vom eigenen Server:
``/einsatzvorbereitung/tiles/<z>/<x>/<y>.png`` liest aus ``TILES_DIR``
(Standard: MEDIA_ROOT/tiles/<z>/<x>/<y>.png). Fehlt eine Kachel, kommt eine
neutrale Platzhalter-Kachel – die Karte bleibt bedienbar, nur ohne Hintergrund.
Kacheln werden auf einer Maschine mit Internet per ``manage.py tiles_download``
geholt und mit ``manage.py tiles_import`` auf der abgeschotteten Maschine eingespielt.
"""
import math
import os
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, HttpResponse

PLACEHOLDER = Path(settings.BASE_DIR) / 'static' / 'img' / 'tile-missing.png'


def tiles_dir():
    return Path(getattr(settings, 'OFFLINE_TILES_DIR', None) or (Path(settings.MEDIA_ROOT) / 'tiles'))


def tile_path(z, x, y):
    return tiles_dir() / str(z) / str(x) / f'{y}.png'


def deg2num(lat, lng, zoom):
    """Koordinate → Kachelindex (x, y) für eine Zoomstufe."""
    lat_rad = math.radians(lat)
    n = 2 ** zoom
    x = int((lng + 180.0) / 360.0 * n)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return max(0, min(n - 1, x)), max(0, min(n - 1, y))


def tile_range(bbox, zoom):
    """(x_min, x_max, y_min, y_max) für Süd,West,Nord,Ost."""
    south, west, north, east = bbox
    x1, y1 = deg2num(north, west, zoom)
    x2, y2 = deg2num(south, east, zoom)
    return min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2)


def count_tiles(bbox, zooms):
    total = 0
    for z in zooms:
        x1, x2, y1, y2 = tile_range(bbox, z)
        total += (x2 - x1 + 1) * (y2 - y1 + 1)
    return total


def tiles_status():
    """Übersicht für die Einstellungsseite: Zoomstufen, Anzahl, Größe."""
    root = tiles_dir()
    zooms = []
    total = 0
    size = 0
    if root.is_dir():
        for zdir in sorted(root.iterdir(), key=lambda p: (not p.name.isdigit(), int(p.name) if p.name.isdigit() else 0)):
            if not zdir.is_dir() or not zdir.name.isdigit():
                continue
            n = 0
            for xdir in zdir.iterdir():
                if xdir.is_dir():
                    for f in os.scandir(xdir):
                        if f.name.endswith('.png'):
                            n += 1
                            size += f.stat().st_size
            zooms.append((int(zdir.name), n))
            total += n
    return {'dir': str(root), 'zooms': zooms, 'total': total, 'size_mb': round(size / 1024 / 1024, 1)}


def tile_response(z, x, y):
    path = tile_path(z, x, y)
    if path.is_file():
        response = FileResponse(open(path, 'rb'), content_type='image/png')
    elif PLACEHOLDER.is_file():
        response = FileResponse(open(PLACEHOLDER, 'rb'), content_type='image/png')
        response['X-Tile-Missing'] = '1'
    else:  # pragma: no cover
        response = HttpResponse(status=404)
    response['Cache-Control'] = 'private, max-age=86400'
    return response
