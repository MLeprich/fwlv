from django import template

register = template.Library()


@register.simple_tag
def gefahren_widget(widget):
    """Daten für das Info-Monitor-Widget „Gefahrenstellen“ (Leitstelle)."""
    from django.utils import timezone
    from ..models import HazardType
    from .. import services

    config = widget.config or {}
    try:
        limit = max(1, min(int(config.get('limit') or 10), 50))
    except (TypeError, ValueError):
        limit = 10
    types = [t for t in (config.get('types') or []) if t in HazardType.values]
    only_restricted = bool(config.get('only_restricted'))
    include_planned = config.get('include_planned', True) not in (False, 'false', '0', 0)

    qs = services.current_hazards(include_planned=include_planned).filter(show_on_monitor=True)
    if types:
        qs = qs.filter(hazard_type__in=types)
    if only_restricted:
        qs = qs.filter(access_restricted=True)
    qs = qs.order_by('-access_restricted', 'start_date', 'title')
    items = list(qs[:limit])
    from .. import handover
    return {'items': items, 'count': qs.count(), 'today': timezone.localdate(),
            'restricted': sum(1 for h in items if h.access_restricted),
            'handover_open': handover.open_count() if config.get('show_handover', True) not in (False, 'false', '0', 0) else None}
