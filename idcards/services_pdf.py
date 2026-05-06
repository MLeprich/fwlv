"""
PDF-Render-Pipeline für Dienstausweise.

Layout-JSON → HTML mit absoluten mm-Positionen → WeasyPrint → PDF.

Wichtige Designentscheidungen:
- Maße in mm. CR80 = 85,6 x 54 mm (Quer) oder 54 x 85,6 mm (Hoch).
- Float-Locale-sicher: f"{x:.2f}" formatiert immer mit Punkt als
  Dezimaltrenner — sonst rendert Django Locale-abhängig "85,6mm" und
  WeasyPrint fällt auf A4 zurück.
- Bilder via Media-Pfad-Reference: src = "media:idcards/assets/<path>".
  Wird beim Render serverseitig zu Data-URL aufgelöst.
"""

from __future__ import annotations

import base64
import io
import logging
import mimetypes
import re
from dataclasses import dataclass

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import formats

from .models import IdCard, IdCardTemplate, IdCardType


logger = logging.getLogger(__name__)


# CR80-Maße in Millimeter
CARD_W_LANDSCAPE = 85.6
CARD_H_LANDSCAPE = 54.0
CARD_W_PORTRAIT = 54.0
CARD_H_PORTRAIT = 85.6

# Pixel-Skala für Web-Vorschau (Display)
DISPLAY_PX_PER_MM = 4.0
PT_PER_MM_RATIO = 1.0 / 0.352778  # 1 mm in pt
PT_TO_PX = 1.333  # 1 pt in CSS px

# Farben pro Ausweis-Typ (für Elemente mit type_color=True)
TYPE_COLORS = {
    IdCardType.REGULAR: '#cc2222',     # Rot
    IdCardType.LEADERSHIP: '#ca8a04',  # Gold
    IdCardType.TRAINEE: '#16a34a',     # Grün
    IdCardType.HONORARY: '#7c3aed',    # Lila
    IdCardType.SPECIAL: '#2563eb',     # Blau
}


_MEDIA_REF_PREFIX = 'media:'


# ============================================================================
# Karten-Geometrie
# ============================================================================


def card_size(template: IdCardTemplate) -> tuple[float, float]:
    """Liefert (width_mm, height_mm) für das Template."""
    if template.is_portrait:
        return CARD_W_PORTRAIT, CARD_H_PORTRAIT
    return CARD_W_LANDSCAPE, CARD_H_LANDSCAPE


# ============================================================================
# Platzhalter-Auflösung
# ============================================================================


_PLACEHOLDER_RE = re.compile(r'\{\{\s*([a-zA-Z_]+)\s*\}\}')


def resolve_placeholders(text: str, card: IdCard) -> str:
    """
    Ersetzt {{key}}-Platzhalter im Text durch Werte aus der Karte/Person.
    """
    if not text or '{{' not in text:
        return text or ''

    person = card.person
    org_name = ''
    try:
        from core.models import SystemSettings
        org_name = SystemSettings.load().organization_name or ''
    except Exception:
        org_name = ''

    issued = formats.date_format(card.issued_at, 'd.m.Y') if card.issued_at else ''
    valid_until = formats.date_format(card.valid_until, 'd.m.Y') if card.valid_until else ''

    rank = card.function_label or getattr(person, 'rank', '') or ''
    function = (
        card.function_label
        or getattr(person, 'function', '')
        or ''
    )

    values = {
        'name': f"{person.first_name} {person.last_name}".strip(),
        'vorname': person.first_name or '',
        'nachname': person.last_name or '',
        'dienstgrad': rank,
        'dienstnummer': person.personnel_number or '',
        'ausweisnummer': card.card_number or '',
        'gueltig_bis': valid_until,
        'ausgestellt_am': issued,
        'organisation': org_name,
        'funktion': function,
        'ausweis_typ': card.get_type_display(),
    }

    def _sub(match: re.Match) -> str:
        return str(values.get(match.group(1).lower(), match.group(0)))

    return _PLACEHOLDER_RE.sub(_sub, text)


# ============================================================================
# Farb-Auflösung
# ============================================================================


def resolve_color(element: dict, card: IdCard) -> str:
    """
    Wenn element.type_color == True, nimm Farbe aus TYPE_COLORS für card.type.
    Sonst element.fill (oder element.color).
    """
    if element.get('type_color'):
        return TYPE_COLORS.get(card.type, element.get('fill') or '#cc2222')
    return element.get('fill') or element.get('color') or '#000000'


# ============================================================================
# Bild-Auflösung (Media-Refs und Person-Foto)
# ============================================================================


def _file_to_data_url(path: str) -> str | None:
    """Lädt eine Datei vom Dateisystem und liefert eine Data-URL (oder None)."""
    try:
        with open(path, 'rb') as fh:
            data = fh.read()
    except (FileNotFoundError, PermissionError, OSError) as e:
        logger.warning('Could not read image %s: %s', path, e)
        return None

    mime, _ = mimetypes.guess_type(path)
    mime = mime or 'image/png'
    encoded = base64.b64encode(data).decode('ascii')
    return f"data:{mime};base64,{encoded}"


def _resolve_media_ref(src: str) -> str | None:
    """
    "media:idcards/assets/logo.png" → MEDIA_ROOT/idcards/assets/logo.png → Data-URL.
    """
    if not src or not src.startswith(_MEDIA_REF_PREFIX):
        return None

    relative = src[len(_MEDIA_REF_PREFIX):].lstrip('/')
    media_root = str(getattr(settings, 'MEDIA_ROOT', ''))
    if not media_root:
        return None

    full_path = f"{media_root.rstrip('/')}/{relative}"
    return _file_to_data_url(full_path)


def _photo_data_url(card: IdCard) -> str | None:
    """Lädt das Personenfoto (id_card_photo, Fallback photo) als Data-URL."""
    person = card.person
    for field in ('id_card_photo', 'photo'):
        img = getattr(person, field, None)
        if img and getattr(img, 'name', ''):
            try:
                path = img.path
            except (ValueError, NotImplementedError):
                path = None
            if path:
                url = _file_to_data_url(path)
                if url:
                    return url
    return None


# ============================================================================
# Layout → Render-Cells
# ============================================================================


@dataclass
class RenderCell:
    """Ein Element bereit zum Rendern in HTML."""
    type: str
    style: str            # Inline-CSS für position/size
    text: str = ''
    image_src: str = ''
    text_style: str = ''  # Inline-CSS für Schriftart/Farbe/etc.
    extra_class: str = ''


def _mm(value: float) -> str:
    """Locale-sichere mm-Formatierung."""
    return f"{float(value):.2f}mm"


def _pos_style(el: dict) -> str:
    """Absolute Positionierung mit Maßen in mm."""
    parts = [
        f"position:absolute",
        f"left:{_mm(el.get('x', 0))}",
        f"top:{_mm(el.get('y', 0))}",
        f"width:{_mm(el.get('w', 10))}",
        f"height:{_mm(el.get('h', 10))}",
    ]
    return ';'.join(parts) + ';'


def _text_style(el: dict, color_override: str | None = None) -> str:
    """Schrift-Inline-Style (font-size, color, weight, align)."""
    parts = [
        f"font-size:{float(el.get('font_size', 8)):.2f}pt",
        f"color:{color_override or el.get('color') or '#000'}",
        f"font-weight:{el.get('weight') or 'normal'}",
        f"text-align:{el.get('align') or 'left'}",
        "line-height:1.15",
    ]
    return ';'.join(parts) + ';'


def build_side_elements(layout: list, card: IdCard) -> list[RenderCell]:
    """
    Übersetzt eine Layout-Liste (Front oder Back) in Render-Cells.
    """
    cells: list[RenderCell] = []
    if not isinstance(layout, list):
        return cells

    for el in layout:
        if not isinstance(el, dict):
            continue
        etype = el.get('type')

        if etype == 'rect':
            color = resolve_color(el, card)
            style = _pos_style(el) + f"background:{color};"
            cells.append(RenderCell(type='rect', style=style))

        elif etype == 'text':
            value = resolve_placeholders(el.get('value', ''), card)
            color = el.get('color') or '#000'
            cells.append(RenderCell(
                type='text',
                style=_pos_style(el) + 'overflow:hidden;',
                text=value,
                text_style=_text_style(el, color_override=color),
            ))

        elif etype == 'photo':
            border_color = el.get('border_color') or '#1a2744'
            border_width = float(el.get('border_width') or 0)
            border_css = (
                f"border:{border_width:.2f}mm solid {border_color};"
                if border_width > 0 else ''
            )
            photo_url = _photo_data_url(card)
            cells.append(RenderCell(
                type='photo',
                style=(
                    _pos_style(el)
                    + 'background:#e2e8f0;'
                    + border_css
                    + 'overflow:hidden;'
                ),
                image_src=photo_url or '',
            ))

        elif etype == 'image':
            url = _resolve_media_ref(el.get('src', '')) or ''
            cells.append(RenderCell(
                type='image',
                style=_pos_style(el) + 'overflow:hidden;',
                image_src=url,
            ))

        # Andere Typen werden ignoriert (z.B. künftige Erweiterungen).

    return cells


# ============================================================================
# Display-Variante (für Bildschirm-Vorschau, mm → px)
# ============================================================================


def _mm_to_px(value: float) -> float:
    return float(value) * DISPLAY_PX_PER_MM


def _pt_to_px(value: float) -> float:
    return float(value) * PT_TO_PX


def _display_pos_style(el: dict) -> str:
    parts = [
        'position:absolute',
        f"left:{_mm_to_px(el.get('x', 0)):.1f}px",
        f"top:{_mm_to_px(el.get('y', 0)):.1f}px",
        f"width:{_mm_to_px(el.get('w', 10)):.1f}px",
        f"height:{_mm_to_px(el.get('h', 10)):.1f}px",
    ]
    return ';'.join(parts) + ';'


def _display_text_style(el: dict, color_override: str | None = None) -> str:
    parts = [
        f"font-size:{_pt_to_px(el.get('font_size', 8)):.1f}px",
        f"color:{color_override or el.get('color') or '#000'}",
        f"font-weight:{el.get('weight') or 'normal'}",
        f"text-align:{el.get('align') or 'left'}",
        'line-height:1.15',
    ]
    return ';'.join(parts) + ';'


def build_card_display(card: IdCard) -> dict:
    """
    Liefert ein Dict mit den Daten für die Web-Vorschau (z.B. Kartendetail-Seite).
    Maße in px (mm × DISPLAY_PX_PER_MM).
    """
    template = card.template
    w_mm, h_mm = card_size(template)

    def side(layout: list) -> list[RenderCell]:
        cells: list[RenderCell] = []
        if not isinstance(layout, list):
            return cells
        for el in layout:
            if not isinstance(el, dict):
                continue
            etype = el.get('type')
            if etype == 'rect':
                color = resolve_color(el, card)
                cells.append(RenderCell(
                    type='rect',
                    style=_display_pos_style(el) + f"background:{color};",
                ))
            elif etype == 'text':
                value = resolve_placeholders(el.get('value', ''), card)
                color = el.get('color') or '#000'
                cells.append(RenderCell(
                    type='text',
                    style=_display_pos_style(el) + 'overflow:hidden;',
                    text=value,
                    text_style=_display_text_style(el, color_override=color),
                ))
            elif etype == 'photo':
                border_color = el.get('border_color') or '#1a2744'
                border_width = float(el.get('border_width') or 0)
                border_px = border_width * DISPLAY_PX_PER_MM
                border_css = (
                    f"border:{border_px:.1f}px solid {border_color};"
                    if border_px > 0 else ''
                )
                photo_url = _photo_data_url(card)
                cells.append(RenderCell(
                    type='photo',
                    style=(
                        _display_pos_style(el)
                        + 'background:#e2e8f0;'
                        + border_css
                        + 'overflow:hidden;'
                    ),
                    image_src=photo_url or '',
                ))
            elif etype == 'image':
                url = _resolve_media_ref(el.get('src', '')) or ''
                cells.append(RenderCell(
                    type='image',
                    style=_display_pos_style(el) + 'overflow:hidden;',
                    image_src=url,
                ))
        return cells

    return {
        'card': card,
        'width_px': _mm_to_px(w_mm),
        'height_px': _mm_to_px(h_mm),
        'front_cells': side(template.front_layout or []),
        'back_cells': side(template.back_layout or []),
    }


# ============================================================================
# WeasyPrint-Render-Funktionen
# ============================================================================


def render_card_html(card: IdCard) -> str:
    """2-seitiges Karten-HTML (Vorder- + Rückseite, je eine @page)."""
    template = card.template
    w_mm, h_mm = card_size(template)

    context = {
        'card': card,
        'card_width_mm': f"{w_mm:.2f}",   # Locale-sicher als String
        'card_height_mm': f"{h_mm:.2f}",
        'front_cells': build_side_elements(template.front_layout or [], card),
        'back_cells': build_side_elements(template.back_layout or [], card),
    }
    return render_to_string('idcards/pdf_card.html', context)


def render_card_pdf(card: IdCard) -> bytes:
    """Rendert einen Einzel-Ausweis (2 Seiten) als PDF-Bytes."""
    from weasyprint import HTML
    html = render_card_html(card)
    pdf = HTML(string=html, base_url=str(getattr(settings, 'MEDIA_ROOT', '/'))).write_pdf()
    return pdf


# ----------------------------------------------------------------------------
# A4-Bogen-Render
# ----------------------------------------------------------------------------


# A4 = 210 x 297 mm
A4_W = 210.0
A4_H = 297.0

# Layout-Konstanten für den Bogen
LANDSCAPE_COLS = 2  # 2 nebeneinander
LANDSCAPE_ROWS = 4  # 4 untereinander → 8 Karten pro Seite
PORTRAIT_COLS = 3   # 3 nebeneinander
PORTRAIT_ROWS = 2   # 2 untereinander → 6 Karten pro Seite


@dataclass
class SheetTile:
    left_mm: float
    top_mm: float
    width_mm: float
    height_mm: float
    card: IdCard | None
    side: str  # 'front' | 'back'


def _grid_positions(card_w: float, card_h: float, cols: int, rows: int, mirror: bool) -> list[tuple[float, float]]:
    """
    Liefert Top-Left-Positionen für eine cols×rows-Anordnung, zentriert auf A4.
    mirror=True spiegelt die Spalten (für die Rückseiten-Wendung).
    """
    block_w = cols * card_w
    block_h = rows * card_h
    margin_x = (A4_W - block_w) / 2.0
    margin_y = (A4_H - block_h) / 2.0

    positions: list[tuple[float, float]] = []
    for r in range(rows):
        for c in range(cols):
            col_idx = (cols - 1 - c) if mirror else c
            x = margin_x + col_idx * card_w
            y = margin_y + r * card_h
            positions.append((x, y))
    return positions


def render_a4_sheet(cards: list[IdCard]) -> bytes:
    """
    Rendert mehrere Karten auf einen A4-Bogen.
    Erste Seite: Vorderseiten. Zweite Seite: Rückseiten (Spalten gespiegelt
    für beidseitigen Druck mit Wendung an Längskante).

    Filtert auf einheitliches Format (Quer ODER Hoch). Bei gemischten Formaten
    werden zwei Bögen-Sets erzeugt (erst Quer, dann Hoch).
    """
    if not cards:
        return b''

    landscape = [c for c in cards if not c.template.is_portrait]
    portrait = [c for c in cards if c.template.is_portrait]

    pdfs: list[bytes] = []
    if landscape:
        pdfs.append(_render_sheet_for_format(
            landscape, CARD_W_LANDSCAPE, CARD_H_LANDSCAPE,
            LANDSCAPE_COLS, LANDSCAPE_ROWS,
        ))
    if portrait:
        pdfs.append(_render_sheet_for_format(
            portrait, CARD_W_PORTRAIT, CARD_H_PORTRAIT,
            PORTRAIT_COLS, PORTRAIT_ROWS,
        ))

    if len(pdfs) == 1:
        return pdfs[0]

    # Mehrere PDFs (Quer + Hoch) zusammenführen.
    return _merge_pdfs(pdfs)


def _render_sheet_for_format(
    cards: list[IdCard],
    card_w: float, card_h: float,
    cols: int, rows: int,
) -> bytes:
    """Rendert alle Karten eines Formats; pro `cols*rows` Karten ein Doppelbogen."""
    from weasyprint import HTML

    per_page = cols * rows
    pages: list[dict] = []

    # Karten in Seitengruppen aufteilen
    for start in range(0, len(cards), per_page):
        chunk = cards[start:start + per_page]

        # Vorderseite: normale Reihenfolge
        front_positions = _grid_positions(card_w, card_h, cols, rows, mirror=False)
        front_tiles: list[dict] = []
        for (x, y), card in zip(front_positions, chunk):
            front_tiles.append({
                'left_mm': f"{x:.2f}",
                'top_mm': f"{y:.2f}",
                'width_mm': f"{card_w:.2f}",
                'height_mm': f"{card_h:.2f}",
                'cells': build_side_elements(card.template.front_layout or [], card),
            })

        # Rückseite: Spalten gespiegelt
        back_positions = _grid_positions(card_w, card_h, cols, rows, mirror=True)
        back_tiles: list[dict] = []
        for (x, y), card in zip(back_positions, chunk):
            back_tiles.append({
                'left_mm': f"{x:.2f}",
                'top_mm': f"{y:.2f}",
                'width_mm': f"{card_w:.2f}",
                'height_mm': f"{card_h:.2f}",
                'cells': build_side_elements(card.template.back_layout or [], card),
            })

        # Schnittlinien (nur wenn mehr als eine Karte)
        cut_lines = _cut_lines(card_w, card_h, cols, rows)

        pages.append({'front_tiles': front_tiles, 'back_tiles': back_tiles, 'cut_lines': cut_lines})

    html = render_to_string('idcards/pdf_a4_sheet.html', {
        'pages': pages,
        'card_width_mm': f"{card_w:.2f}",
        'card_height_mm': f"{card_h:.2f}",
    })
    return HTML(string=html, base_url=str(getattr(settings, 'MEDIA_ROOT', '/'))).write_pdf()


def _cut_lines(card_w: float, card_h: float, cols: int, rows: int) -> list[dict]:
    """Gestrichelte Schnittlinien zwischen den Karten (vertikale Trenner)."""
    block_w = cols * card_w
    block_h = rows * card_h
    margin_x = (A4_W - block_w) / 2.0
    margin_y = (A4_H - block_h) / 2.0

    lines: list[dict] = []
    # Vertikale Linien (zwischen Spalten)
    for c in range(1, cols):
        x = margin_x + c * card_w
        lines.append({
            'orient': 'vertical',
            'left_mm': f"{x:.2f}",
            'top_mm': f"{margin_y:.2f}",
            'length_mm': f"{block_h:.2f}",
        })
    # Horizontale Linien (zwischen Zeilen)
    for r in range(1, rows):
        y = margin_y + r * card_h
        lines.append({
            'orient': 'horizontal',
            'left_mm': f"{margin_x:.2f}",
            'top_mm': f"{y:.2f}",
            'length_mm': f"{block_w:.2f}",
        })
    return lines


def render_single_card_a4(card: IdCard, copies: int = 8) -> bytes:
    """Eine Karte N-mal auf einem A4-Bogen."""
    return render_a4_sheet([card] * max(1, int(copies)))


# ============================================================================
# PDF-Merge
# ============================================================================


def _merge_pdfs(pdfs: list[bytes]) -> bytes:
    """Multi-Sheet-Merge via pypdf."""
    from pypdf import PdfReader, PdfWriter

    writer = PdfWriter()
    for raw in pdfs:
        reader = PdfReader(io.BytesIO(raw))
        for page in reader.pages:
            writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def merge_card_pdfs(cards: list[IdCard]) -> bytes:
    """Mehrere Einzelkarten-PDFs (je 2 Seiten) zu einem Dokument zusammenführen."""
    pdfs = [render_card_pdf(c) for c in cards]
    return _merge_pdfs(pdfs) if pdfs else b''
