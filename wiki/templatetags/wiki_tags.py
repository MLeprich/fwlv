from django import template

from ..text import render_inline

register = template.Library()


@register.filter(name='wikitext')
def wikitext(value):
    """Absatztext mit einfacher Auszeichnung (**fett**, *kursiv*, `Code`, Links, [[Wiki-Seite]])."""
    return render_inline(value)


@register.filter(name='wikitext_plain')
def wikitext_plain(value):
    """Wie wikitext, aber ohne Wiki-Link-Auflösung (z.B. für Vorschauen ohne DB-Zugriff)."""
    return render_inline(value, wiki_links=False)


@register.filter
def filesize_display(value):
    try:
        size = int(value)
    except (TypeError, ValueError):
        return value or ''
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024 or unit == 'GB':
            return f'{size:.0f} {unit}' if unit == 'B' else f'{size:.1f} {unit}'
        size /= 1024
    return value
