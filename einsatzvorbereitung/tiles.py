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
import shutil
import zipfile
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


# ---------------------------------------------------------------------------
# Einspielen (Upload im Browser oder manage.py tiles_import)
# ---------------------------------------------------------------------------

PNG_MAGIC = (b'\x89PNG',)
JPEG_MAGIC = (b'\xff\xd8\xff',)


def _looks_like_tile(data):
    return data[:4] in PNG_MAGIC or data[:3] in JPEG_MAGIC


def tile_parts(path_text):
    """„…/13/4252/2724.png“ → (13, 4252, 2724) oder None (nur z/x/y.png wird akzeptiert)."""
    parts = [p for p in str(path_text).replace('\\', '/').split('/') if p and p != '.']
    if len(parts) < 3:
        return None
    z, x, y = parts[-3], parts[-2], parts[-1]
    if not (z.isdigit() and x.isdigit()):
        return None
    name, dot, ext = y.rpartition('.')
    if not dot or ext.lower() not in ('png', 'jpg', 'jpeg') or not name.isdigit():
        return None
    return int(z), int(x), int(name)


def store_tile(z, x, y, data, out=None):
    """Eine Kachel ablegen (immer als <y>.png); liefert True bei Erfolg."""
    if not _looks_like_tile(data):
        return False
    target = (out or tiles_dir()) / str(z) / str(x) / f'{y}.png'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return True


def clear_tiles(out=None):
    root = out or tiles_dir()
    if root.is_dir():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)


def import_zip(fileobj, out=None, replace=False):
    """ZIP mit z/x/y.png-Struktur (beliebig tief verschachtelt) einspielen; liefert (eingespielt, übersprungen)."""
    out = out or tiles_dir()
    if replace:
        clear_tiles(out)
    imported = skipped = 0
    with zipfile.ZipFile(fileobj) as zf:
        for member in zf.namelist():
            if member.endswith('/'):
                continue  # Ordnereinträge zählen nicht als übersprungene Dateien
            parts = tile_parts(member)
            if parts is None:
                skipped += 1
                continue
            with zf.open(member) as f:
                data = f.read()
            if store_tile(*parts, data, out=out):
                imported += 1
            else:
                skipped += 1
    return imported, skipped


def import_files(files_with_paths, out=None, replace=False):
    """Lose Kacheln aus einem Ordner-Upload: [(relativer Pfad, Dateiobjekt), …]."""
    out = out or tiles_dir()
    if replace:
        clear_tiles(out)
    imported = skipped = 0
    for rel_path, f in files_with_paths:
        parts = tile_parts(rel_path)
        if parts is None:
            skipped += 1
            continue
        data = f.read()
        if store_tile(*parts, data, out=out):
            imported += 1
        else:
            skipped += 1
    return imported, skipped
