"""
Wiki – Textverarbeitung ohne Zusatzpakete

* ``render_inline``: leichte Auszeichnung in Absätzen (**fett**, *kursiv*, `Code`,
  [Text](URL), [[Wiki-Seite]]) – der Text wird zuerst HTML-escaped, danach werden
  nur die erkannten Muster in sichere Tags umgesetzt.
* ``markdown_to_blocks``: eingefügten Markdown-Text in Editor-Blöcke zerlegen
  (Überschriften, Absätze, Listen, Checklisten, Zitate, Code, Tabellen, Bilder, Trennlinien).
* ``block_plain_text`` / ``page_plain_text``: Volltext für die Suche.
* ``PAGE_TEMPLATES``: Seitenvorlagen für Anleitungen, Checklisten, FAQ …
"""
import re

from django.utils.html import escape
from django.utils.safestring import mark_safe

_INLINE_CODE = re.compile(r'`([^`]+)`')
_BOLD = re.compile(r'\*\*(.+?)\*\*')
_ITALIC = re.compile(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])')
_LINK = re.compile(r'\[([^\]]+)\]\(([^)\s]+)\)')
_WIKI_LINK = re.compile(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')
_AUTOLINK = re.compile(r'(?<![">])(https?://[^\s<]+)')
_SAFE_URL = re.compile(r'^(https?://|mailto:|tel:|/|#)', re.I)


def _wiki_page_url(target):
    """[[Titel]] oder [[slug]] → (URL, Titel) oder (None, Titel)."""
    from .models import WikiPage
    target = target.strip()
    page = (WikiPage.objects.filter(is_deleted=False).filter(slug=target).first()
            or WikiPage.objects.filter(is_deleted=False, title__iexact=target).first())
    if page:
        return page.get_absolute_url(), page.title
    return None, target


def render_inline(text, wiki_links=True):
    """Escaped Text mit einfacher Auszeichnung; Zeilenumbrüche werden zu <br>."""
    if not text:
        return ''
    html = escape(str(text))

    def link(m):
        label, url = m.group(1), m.group(2)
        if not _SAFE_URL.match(url):
            return label
        external = url.lower().startswith('http')
        target = ' target="_blank" rel="noopener"' if external else ''
        return f'<a href="{url}" class="text-primary-600 underline hover:text-primary-800"{target}>{label}</a>'

    def wiki(m):
        url, title = _wiki_page_url(m.group(1))
        label = m.group(2) or title
        if url:
            return f'<a href="{url}" class="text-primary-600 underline hover:text-primary-800">{label}</a>'
        return f'<span class="text-gray-500 border-b border-dashed border-gray-400" title="Seite „{title}“ gibt es noch nicht">{label}</span>'

    html = _INLINE_CODE.sub(r'<code class="px-1 py-0.5 bg-gray-100 rounded text-sm font-mono">\1</code>', html)
    html = _BOLD.sub(r'<strong>\1</strong>', html)
    html = _ITALIC.sub(r'<em>\1</em>', html)
    html = _LINK.sub(link, html)
    if wiki_links:
        html = _WIKI_LINK.sub(wiki, html)
    html = _AUTOLINK.sub(r'<a href="\1" class="text-primary-600 underline hover:text-primary-800" target="_blank" rel="noopener">\1</a>', html)
    return mark_safe(html.replace('\n', '<br>'))


# ---------------------------------------------------------------------------
# Volltext
# ---------------------------------------------------------------------------

def block_plain_text(block_type, content):
    """Alle sichtbaren Texte eines Blocks als eine Zeichenkette."""
    c = content or {}
    parts = []

    def add(value):
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
        elif isinstance(value, list):
            for v in value:
                add(v)
        elif isinstance(value, dict):
            for key in ('text', 'title', 'caption', 'alt', 'filename', 'description', 'linkText', 'pageTitle', 'code'):
                add(value.get(key))

    for key in ('text', 'title', 'caption', 'alt', 'filename', 'description', 'linkText', 'pageTitle', 'code'):
        add(c.get(key))
    add(c.get('items'))
    add(c.get('steps'))
    add(c.get('headers'))
    add(c.get('rows'))
    add(c.get('columns'))
    return ' '.join(parts)


def page_plain_text(blocks):
    return '\n'.join(t for t in (block_plain_text(b.block_type, b.content) for b in blocks) if t)


# ---------------------------------------------------------------------------
# Markdown → Blöcke
# ---------------------------------------------------------------------------

_HEADING = re.compile(r'^(#{1,3})\s+(.*)$')
_CHECK = re.compile(r'^\s*[-*+]\s+\[([ xX])\]\s+(.*)$')
_BULLET = re.compile(r'^\s*[-*+]\s+(.*)$')
_NUMBERED = re.compile(r'^\s*\d+[.)]\s+(.*)$')
_IMAGE = re.compile(r'^!\[([^\]]*)\]\(([^)\s]+)\)\s*$')
_TABLE_SEP = re.compile(r'^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$')
_CALLOUT = re.compile(r'^>\s*\[!(INFO|WARNUNG|WARNING|TIPP|TIP|ACHTUNG|FEHLER|ERROR)\]\s*(.*)$', re.I)


def _split_row(line):
    line = line.strip()
    if line.startswith('|'):
        line = line[1:]
    if line.endswith('|'):
        line = line[:-1]
    return [c.strip() for c in line.split('|')]


def markdown_to_blocks(text):
    """Liefert [(block_type, content, style_options), …]; unbekannte Zeilen werden Absätze."""
    lines = (text or '').replace('\r\n', '\n').replace('\r', '\n').split('\n')
    blocks = []
    paragraph = []
    i = 0

    def flush_paragraph():
        if paragraph:
            blocks.append(('paragraph', {'text': '\n'.join(paragraph).strip()}, {}))
            paragraph.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            i += 1
            continue

        if stripped.startswith('```'):
            flush_paragraph()
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code.append(lines[i])
                i += 1
            blocks.append(('code', {'code': '\n'.join(code)}, {}))
            i += 1
            continue

        m = _HEADING.match(stripped)
        if m:
            flush_paragraph()
            blocks.append((f'heading_{len(m.group(1))}', {'text': m.group(2).strip()}, {}))
            i += 1
            continue

        if stripped in ('---', '***', '___'):
            flush_paragraph()
            blocks.append(('divider', {}, {}))
            i += 1
            continue

        m = _IMAGE.match(stripped)
        if m:
            flush_paragraph()
            blocks.append(('image', {'url': m.group(2), 'alt': m.group(1), 'caption': m.group(1)}, {}))
            i += 1
            continue

        m = _CALLOUT.match(stripped)
        if m:
            flush_paragraph()
            kind = m.group(1).upper()
            typ = {'WARNUNG': 'warning', 'WARNING': 'warning', 'ACHTUNG': 'warning',
                   'FEHLER': 'error', 'ERROR': 'error'}.get(kind, 'info')
            body = [m.group(2)]
            i += 1
            while i < len(lines) and lines[i].strip().startswith('>'):
                body.append(lines[i].strip()[1:].strip())
                i += 1
            title = 'Hinweis' if typ == 'info' else ('Warnung' if typ == 'warning' else 'Achtung')
            blocks.append(('alert', {'type': typ, 'title': title, 'text': '\n'.join(b for b in body if b).strip()}, {}))
            continue

        if stripped.startswith('>'):
            flush_paragraph()
            body = []
            while i < len(lines) and lines[i].strip().startswith('>') and not _CALLOUT.match(lines[i].strip()):
                body.append(lines[i].strip()[1:].strip())
                i += 1
            blocks.append(('quote', {'text': '\n'.join(body).strip()}, {}))
            continue

        if _CHECK.match(stripped):
            flush_paragraph()
            items = []
            while i < len(lines) and _CHECK.match(lines[i].strip()):
                m = _CHECK.match(lines[i].strip())
                items.append({'text': m.group(2).strip(), 'checked': m.group(1).lower() == 'x'})
                i += 1
            blocks.append(('checklist', {'items': items}, {}))
            continue

        if _BULLET.match(stripped):
            flush_paragraph()
            items = []
            while i < len(lines) and _BULLET.match(lines[i].strip()) and not _CHECK.match(lines[i].strip()):
                items.append({'text': _BULLET.match(lines[i].strip()).group(1).strip()})
                i += 1
            blocks.append(('bullet_list', {'items': items}, {}))
            continue

        if _NUMBERED.match(stripped):
            flush_paragraph()
            items = []
            while i < len(lines) and _NUMBERED.match(lines[i].strip()):
                items.append({'text': _NUMBERED.match(lines[i].strip()).group(1).strip()})
                i += 1
            blocks.append(('numbered_list', {'items': items}, {}))
            continue

        if '|' in stripped and i + 1 < len(lines) and _TABLE_SEP.match(lines[i + 1]):
            flush_paragraph()
            headers = _split_row(stripped)
            i += 2
            rows = []
            while i < len(lines) and '|' in lines[i] and lines[i].strip():
                row = _split_row(lines[i])
                row = (row + [''] * len(headers))[:len(headers)]
                rows.append(row)
                i += 1
            blocks.append(('table', {'headers': headers, 'rows': rows}, {}))
            continue

        paragraph.append(stripped)
        i += 1

    flush_paragraph()
    return blocks


# ---------------------------------------------------------------------------
# Seitenvorlagen
# ---------------------------------------------------------------------------

PAGE_TEMPLATES = {
    'leer': {
        'label': 'Leere Seite', 'icon': '📄',
        'description': 'Ohne Vorgaben – Blöcke frei zusammenstellen.',
        'blocks': [],
    },
    'anleitung': {
        'label': 'Anleitung (Schritt für Schritt)', 'icon': '🧭',
        'description': 'Ziel, Voraussetzungen, nummerierte Schritte mit Bild, Hinweise und Fehlerbehebung.',
        'blocks': [
            ('callout', {'icon': '🎯', 'title': 'Worum geht es?', 'text': 'Kurz beschreiben, was mit dieser Anleitung erreicht wird und für wen sie gedacht ist.'}, {'color': 'blue'}),
            ('heading_2', {'text': 'Voraussetzungen'}, {}),
            ('bullet_list', {'items': [{'text': 'Benötigte Geräte, Zugänge oder Unterlagen'}, {'text': '…'}]}, {}),
            ('heading_2', {'text': 'Schritte'}, {}),
            ('steps', {'steps': [{'title': 'Erster Schritt', 'text': 'Was genau ist zu tun?', 'image': ''},
                                 {'title': 'Zweiter Schritt', 'text': '', 'image': ''}]}, {}),
            ('alert', {'type': 'warning', 'title': 'Achtung', 'text': 'Worauf muss besonders geachtet werden?'}, {}),
            ('heading_2', {'text': 'Wenn etwas nicht klappt'}, {}),
            ('accordion', {'title': 'Problem: …', 'text': 'Lösung: …'}, {}),
        ],
    },
    'checkliste': {
        'label': 'Checkliste', 'icon': '☑️',
        'description': 'Abhakbare Punkte, z.B. für Prüfungen, Übergaben oder Vorbereitungen.',
        'blocks': [
            ('paragraph', {'text': 'Wann und von wem ist diese Checkliste zu verwenden?'}, {}),
            ('heading_2', {'text': 'Vorbereitung'}, {}),
            ('checklist', {'items': [{'text': 'Punkt 1', 'checked': False}, {'text': 'Punkt 2', 'checked': False}]}, {}),
            ('heading_2', {'text': 'Durchführung'}, {}),
            ('checklist', {'items': [{'text': 'Punkt 1', 'checked': False}]}, {}),
            ('heading_2', {'text': 'Abschluss'}, {}),
            ('checklist', {'items': [{'text': 'Dokumentation erledigt', 'checked': False}]}, {}),
        ],
    },
    'faq': {
        'label': 'FAQ / Fragen & Antworten', 'icon': '❓',
        'description': 'Aufklappbare Fragen mit Antworten.',
        'blocks': [
            ('paragraph', {'text': 'Häufige Fragen zu …'}, {}),
            ('accordion', {'title': 'Frage 1?', 'text': 'Antwort …'}, {}),
            ('accordion', {'title': 'Frage 2?', 'text': 'Antwort …'}, {}),
            ('accordion', {'title': 'Frage 3?', 'text': 'Antwort …'}, {}),
        ],
    },
    'stoerung': {
        'label': 'Störung / Problemlösung', 'icon': '🛠️',
        'description': 'Symptom, mögliche Ursachen, Sofortmaßnahmen, dauerhafte Lösung, Ansprechpartner.',
        'blocks': [
            ('alert', {'type': 'warning', 'title': 'Symptom', 'text': 'Was wird beobachtet? Wann tritt es auf?'}, {}),
            ('heading_2', {'text': 'Sofortmaßnahmen'}, {}),
            ('numbered_list', {'items': [{'text': 'Erste Maßnahme'}, {'text': 'Zweite Maßnahme'}]}, {}),
            ('heading_2', {'text': 'Mögliche Ursachen'}, {}),
            ('table', {'headers': ['Ursache', 'Prüfung', 'Behebung'], 'rows': [['', '', '']]}, {}),
            ('heading_2', {'text': 'Ansprechpartner'}, {}),
            ('paragraph', {'text': 'Wer hilft weiter? Telefon, Erreichbarkeit.'}, {}),
        ],
    },
    'geraet': {
        'label': 'Gerät / Ausstattung', 'icon': '🧰',
        'description': 'Steckbrief mit Daten, Bedienung, Prüfung und Dokumenten.',
        'blocks': [
            ('table', {'headers': ['Merkmal', 'Wert'], 'rows': [['Hersteller / Typ', ''], ['Standort', ''], ['Prüfintervall', ''], ['Verantwortlich', '']]}, {}),
            ('heading_2', {'text': 'Bedienung'}, {}),
            ('steps', {'steps': [{'title': 'Inbetriebnahme', 'text': '', 'image': ''}, {'title': 'Außerbetriebnahme', 'text': '', 'image': ''}]}, {}),
            ('heading_2', {'text': 'Prüfung & Wartung'}, {}),
            ('checklist', {'items': [{'text': 'Sichtprüfung', 'checked': False}, {'text': 'Funktionsprüfung', 'checked': False}]}, {}),
            ('heading_2', {'text': 'Dokumente'}, {}),
            ('file', {'url': '', 'filename': '', 'filesize': '', 'description': 'Bedienungsanleitung des Herstellers'}, {}),
        ],
    },
}
