"""
Custom template tags for diving app.
"""
from django import template

register = template.Library()


@register.filter(name='get_field')
def get_field(form, field_name):
    """
    Returns a form field by name.
    Usage: {{ form|get_field:"field_name" }}
    """
    try:
        return form[field_name]
    except KeyError:
        return ''


@register.filter(name='get_field_value')
def get_field_value(form, field_name):
    """
    Returns the value of a form field by name.
    Usage: {{ form|get_field_value:"field_name" }}
    """
    try:
        field = form[field_name]
        return field.value()
    except KeyError:
        return None


@register.simple_tag
def checklist_progress(form):
    """
    Returns the progress of checklist completion.
    Usage: {% checklist_progress form %}
    """
    if not hasattr(form, 'checklist_items'):
        return {'total': 0, 'checked': 0, 'percentage': 0}

    total = len(form.checklist_items)
    if total == 0:
        return {'total': 0, 'checked': 0, 'percentage': 0}

    checked = sum(
        1 for item in form.checklist_items
        if form.cleaned_data.get(item['field_name'], False)
    ) if hasattr(form, 'cleaned_data') else 0

    percentage = round((checked / total) * 100) if total > 0 else 0

    return {
        'total': total,
        'checked': checked,
        'percentage': percentage
    }
