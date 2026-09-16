from django import template

register = template.Library()

COLOR_CLASSES = {
    'gray': 'bg-gray-100 text-gray-800 border-gray-300',
    'blue': 'bg-blue-100 text-blue-800 border-blue-300',
    'green': 'bg-green-100 text-green-800 border-green-300',
    'yellow': 'bg-yellow-100 text-yellow-800 border-yellow-300',
    'orange': 'bg-orange-100 text-orange-800 border-orange-300',
    'red': 'bg-red-100 text-red-800 border-red-300',
    'purple': 'bg-purple-100 text-purple-800 border-purple-300',
}
DOT_CLASSES = {
    'gray': 'bg-gray-400', 'blue': 'bg-blue-500', 'green': 'bg-green-500', 'yellow': 'bg-yellow-400',
    'orange': 'bg-orange-500', 'red': 'bg-red-500', 'purple': 'bg-purple-500',
}


@register.filter
def category_classes(category):
    return COLOR_CLASSES.get(getattr(category, 'color', 'gray'), COLOR_CLASSES['gray'])


@register.filter
def category_dot(category):
    return DOT_CLASSES.get(getattr(category, 'color', 'gray'), DOT_CLASSES['gray'])


@register.simple_tag
def kalender_widget(widget):
    """Daten für das Info-Monitor-Widget „Kalender“."""
    from django.utils import timezone
    from .. import services
    config = widget.config or {}
    try:
        days = max(1, min(int(config.get('days') or 14), 90))
    except (TypeError, ValueError):
        days = 14
    try:
        limit = max(1, min(int(config.get('limit') or 12), 50))
    except (TypeError, ValueError):
        limit = 12
    categories = [int(c) for c in (config.get('categories') or []) if str(c).isdigit()]
    sites = [int(s) for s in (config.get('sites') or []) if str(s).isdigit()]
    public_only = bool(getattr(widget.dashboard, 'is_public', False))
    items = services.upcoming(days=days, limit=limit, categories=categories or None, sites=sites or None,
                              monitor_only=True, public_only=public_only)
    today = timezone.localdate()
    grouped = []
    for o in items:
        day = max(o.start, today)
        if grouped and grouped[-1]['date'] == day:
            grouped[-1]['items'].append(o)
        else:
            grouped.append({'date': day, 'items': [o]})
    return {'days': days, 'today': today, 'groups': grouped, 'count': len(items)}
