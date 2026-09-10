"""
Brandverhütungsschau – Import der Mustersätze aus der PDF-Vorlage

Die Vorlage „Mustersätze für Stellungnahmen“ ist ein Word-Export mit
Kopf-/Fußzeilen, Inhaltsverzeichnis und Randkommentaren aus der
Überarbeitung („Kommentiert [HD5]: …“). Der Parser arbeitet auf der
Ausgabe von ``pdftotext -layout`` und liefert Kapitel, Abschnitte und die
nummerierten Mustersätze. Randkommentare werden aus dem Text entfernt und
als Prüfhinweis zurückgegeben, damit sie nach dem Import durchgesehen
werden können.
"""

import re
import shutil
import subprocess
from dataclasses import dataclass, field

HEADER_END = 'Vorbeugender Brandschutz'
HEADER_MAX_LINES = 8

_RE_TOC = re.compile(r'\.{5,}')
_RE_FOOTER = re.compile(r'^\s*(\d+\s+)?Stand:\s*\d{2}\.\d{2}\.\d{4}(\s+\d+)?\s*$')
_RE_COMMENT = re.compile(r'\s{2,}Kommentiert \[[^\]]+\]:\s*(.*)$')
_RE_CHAPTER = re.compile(r'^(\d{1,2})\.\s{2,}(\S.*)$')
_RE_SECTION = re.compile(r'^(\d{1,2}\.\d{1,2})\s{2,}(\S.*)$')
_RE_PHRASE = re.compile(r'^(\d{4,5})(?:\s{2,}(\S.*))?$')
_RE_SPACES = re.compile(r'\s{2,}')

#: Ab dieser Einrückung gilt eine Zeile als Aufzählungspunkt (Randkommentare
#: stehen deutlich weiter rechts und werden vorher entfernt).
LIST_INDENT = 4
#: Zeilen, deren Text erst ab dieser Spalte beginnt, gehören zur Randspalte.
MARGIN_COLUMN = 60


@dataclass
class ParsedPhrase:
    code: str
    title: str
    category: str  # Nummer des Kapitels bzw. Abschnitts
    paragraphs: list = field(default_factory=list)
    notes: list = field(default_factory=list)

    @property
    def text(self):
        return '\n\n'.join(p for p in self.paragraphs if p)


@dataclass
class ParsedCategory:
    number: str
    title: str
    parent: str = ''  # Nummer des Kapitels (nur bei Abschnitten)
    notes: list = field(default_factory=list)


@dataclass
class ParseResult:
    categories: list = field(default_factory=list)
    phrases: list = field(default_factory=list)


def pdf_to_text(path):
    """PDF → Text mit erhaltenem Layout (poppler-utils)."""
    if not shutil.which('pdftotext'):
        raise RuntimeError('pdftotext (poppler-utils) ist nicht installiert.')
    result = subprocess.run(
        ['pdftotext', '-layout', '-enc', 'UTF-8', str(path), '-'],
        capture_output=True, check=True,
    )
    return result.stdout.decode('utf-8')


def _strip_page(page):
    """Kopfzeilen (bis „Vorbeugender Brandschutz“) und Fußzeile entfernen."""
    lines = page.split('\n')
    for i, line in enumerate(lines[:HEADER_MAX_LINES]):
        if HEADER_END in line:
            lines = lines[i + 1:]
            break
    return [line for line in lines if not _RE_FOOTER.match(line)]


class _CommentTracker:
    """
    Entfernt Randkommentare. Ein Kommentar beginnt mit „Kommentiert [..]:“
    und kann in den Folgezeilen in derselben Spalte weiterlaufen – teils
    allein, teils rechts neben Fließtext.
    """

    def __init__(self):
        self.column = None
        self.current = None

    def process(self, line):
        """
        → (Zeile ohne Kommentar, neuer Kommentar oder None, nur Kommentar?).
        Der Kommentar ist eine Liste, an die Folgezeilen noch angehängt werden.
        """
        match = _RE_COMMENT.search(line)
        if match:
            self.column = match.start() + len(match.group(0)) - len(match.group(0).lstrip())
            self.current = [match.group(1).strip()]
            rest = line[:match.start()].rstrip()
            return rest, self.current, not rest.strip()
        if self.column is not None:
            tail_start = self._tail_start(line)
            if tail_start is not None:
                self.current.append(line[tail_start:].strip())
                rest = line[:tail_start].rstrip()
                return rest, None, not rest.strip()
            self.column = None
            self.current = None
        return line, None, False

    def _tail_start(self, line):
        if len(line) <= self.column - 3 or not line[self.column - 3:].strip():
            return None
        head = line[:self.column - 3]
        if not head.strip():
            return len(line) - len(line.lstrip())
        gap = re.search(r'\s{3,}(?=\S)', line[len(head.rstrip()):])
        if gap is None:
            return None
        start = len(head.rstrip()) + gap.end()
        return start if start >= self.column - 3 else None


def _join_lines(lines):
    text = ''
    for line in lines:
        line = _RE_SPACES.sub(' ', line.strip())
        if not line:
            continue
        if not text:
            text = line
        elif re.search(r'[A-Za-zÄÖÜäöüß]-$', text) and line[:1].isupper():
            text += line  # „Ist-\nZustand“ → „Ist-Zustand“
        else:
            text += ' ' + line
    return text


def parse_text(text):
    """Text der Vorlage → ParseResult (Kapitel, Abschnitte, Mustersätze)."""
    result = ParseResult()
    chapter = None
    category = None
    phrase = None
    paragraph = []
    paragraph_is_item = False
    comments = _CommentTracker()

    def flush_paragraph():
        nonlocal paragraph, paragraph_is_item
        if phrase is not None and paragraph:
            joined = _join_lines(paragraph)
            if joined:
                phrase.paragraphs.append(f'– {joined}' if paragraph_is_item else joined)
        paragraph = []
        paragraph_is_item = False

    for page in text.split('\f'):
        for raw in _strip_page(page):
            if _RE_TOC.search(raw):
                continue
            line, comment, comment_only = comments.process(raw)
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())

            if not stripped:
                # Eine reine Kommentarzeile kann eine Leerzeile verdecken – mitten
                # im Satz trennt sie aber keinen Absatz.
                if not comment_only or (paragraph and paragraph[-1].rstrip().endswith(('.', '!', '?', ':'))):
                    flush_paragraph()
                if comment is not None and phrase is not None:
                    phrase.notes.append(comment)
                continue

            m_chapter = _RE_CHAPTER.match(stripped)
            # Kapitel sind fortlaufend nummeriert – das schützt vor Fließtext, der mit „12.“ beginnt
            if indent == 0 and m_chapter and (chapter is None or int(m_chapter.group(1)) == int(chapter.number) + 1):
                flush_paragraph()
                phrase = None
                chapter = ParsedCategory(m_chapter.group(1), m_chapter.group(2).strip())
                category = chapter
                result.categories.append(chapter)
                if comment is not None:
                    chapter.notes.append(comment)
                continue
            if chapter is None:
                continue  # Titelblatt / Inhaltsverzeichnis

            m_section = _RE_SECTION.match(stripped)
            if indent == 0 and m_section and m_section.group(1).split('.')[0] == chapter.number:
                flush_paragraph()
                phrase = None
                category = ParsedCategory(m_section.group(1), m_section.group(2).strip(), parent=chapter.number)
                result.categories.append(category)
                if comment is not None:
                    category.notes.append(comment)
                continue

            m_phrase = _RE_PHRASE.match(stripped)
            if indent == 0 and m_phrase and m_phrase.group(1).startswith(chapter.number) \
                    and (phrase is None or int(m_phrase.group(1)) > int(phrase.code)):
                flush_paragraph()
                phrase = ParsedPhrase(m_phrase.group(1), (m_phrase.group(2) or '').strip(), category.number)
                result.phrases.append(phrase)
                if comment is not None:
                    phrase.notes.append(comment)
                continue

            if phrase is None:
                continue
            if comment is not None:
                phrase.notes.append(comment)
            if indent >= MARGIN_COLUMN:
                continue  # Rest der Randspalte ohne erkannten Kommentar
            if indent >= LIST_INDENT and not paragraph:
                paragraph_is_item = True
            paragraph.append(line)

    flush_paragraph()
    return result


def parse_pdf(path):
    return parse_text(pdf_to_text(path))


def note_text(notes):
    """Kommentarlisten → lesbarer Prüfhinweis."""
    return '\n'.join('Randkommentar: ' + ' '.join(part for part in note if part) for note in notes)
