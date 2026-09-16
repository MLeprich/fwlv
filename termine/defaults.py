"""Vorbelegte Terminkategorien (können in der Kategorieverwaltung geändert werden)."""

DEFAULT_CATEGORIES = [
    # name, color, icon, sort_order
    ('Übung', 'red', '🚒', 10),
    ('Lehrgang', 'blue', '🎓', 20),
    ('Sitzung', 'purple', '🗣️', 30),
    ('Veranstaltung', 'green', '🎉', 40),
    ('Wartung / Prüfung', 'orange', '🔧', 50),
    ('Sonstiges', 'gray', '📌', 90),
]


def ensure_default_categories(EventCategory):
    if EventCategory.objects.exists():
        return 0
    created = 0
    for name, color, icon, order in DEFAULT_CATEGORIES:
        EventCategory.objects.get_or_create(name=name, defaults={'color': color, 'icon': icon, 'sort_order': order})
        created += 1
    return created
