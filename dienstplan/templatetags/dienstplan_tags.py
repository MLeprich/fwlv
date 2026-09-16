from django import template

register = template.Library()

COLOR_CLASSES = {
    'gray': 'bg-gray-100 text-gray-700',
    'blue': 'bg-blue-100 text-blue-800',
    'green': 'bg-green-100 text-green-800',
    'yellow': 'bg-yellow-100 text-yellow-800',
    'orange': 'bg-orange-100 text-orange-800',
    'red': 'bg-red-100 text-red-800',
    'purple': 'bg-purple-100 text-purple-800',
}


@register.filter
def code_classes(duty):
    """Tailwind-Klassen für einen DutyCode (oder Rohcode als String)."""
    color = getattr(duty, 'color', 'gray') if duty else 'gray'
    return COLOR_CLASSES.get(color, COLOR_CLASSES['gray'])


@register.filter
def code_text(duty):
    if duty is None:
        return ''
    return getattr(duty, 'code', duty)


@register.filter
def code_title(duty):
    if duty is None:
        return ''
    return getattr(duty, 'label', duty)


@register.filter
def get_item(mapping, key):
    try:
        return mapping.get(key)
    except AttributeError:
        return None


@register.simple_tag
def dienstplan_widget(widget):
    """Daten für das Info-Monitor-Widget: heute (Funktion → Namen) oder 7-Tage-Tabelle."""
    from django.utils import timezone
    from .. import services
    from ..models import DutyFunction
    config = widget.config or {}
    functions = [f for f in (config.get('functions') or []) if f in DutyFunction.values] or list(DutyFunction.values)
    labels = dict(DutyFunction.choices)
    today = timezone.localdate()
    if config.get('mode') == 'week':
        days = services.fuehrungsdienst_range(today, 7)
        return {
            'mode': 'week', 'today': today,
            'functions': [(f, labels[f]) for f in functions],
            'days': [{'date': d['date'], 'cells': [d['functions'].get(f, []) for f in functions]} for d in days],
            'has_plan': any(d['functions'] for d in days),
        }
    plan = services.fuehrungsdienst_for(today)
    return {
        'mode': 'today', 'today': today,
        'rows': [(labels[f], plan.get(f, [])) for f in functions],
        'has_plan': services.has_plan_for(today),
    }
