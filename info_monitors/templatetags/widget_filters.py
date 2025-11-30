"""
Custom template filters for Info Monitors widgets
"""
from django import template

register = template.Library()


@register.filter
def parse_events(content):
    """
    Parse events from text format: YYYY-MM-DD | Title | Description
    Returns list of event dictionaries
    """
    if not content:
        return []

    events = []
    for line in content.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 2:
            event = {
                'date': parts[0] if len(parts) > 0 else '',
                'title': parts[1] if len(parts) > 1 else '',
                'description': parts[2] if len(parts) > 2 else '',
            }
            events.append(event)

    return events
