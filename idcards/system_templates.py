"""
System-Templates für Dienstausweise.

Werden idempotent angelegt/überschrieben durch ensure_system_templates().
System-Templates sind im Editor schreibgeschützt — Nutzer dupliziert zum Anpassen.

Maße:
    CR80 Querformat: 85.6 x 54 mm
    CR80 Hochformat: 54 x 85.6 mm
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction

from .models import IdCardTemplate


User = get_user_model()


# ----------------------------------------------------------------------------
# Layouts
# ----------------------------------------------------------------------------


def _navy_landscape_front() -> list[dict]:
    return [
        # Navy-Header
        {"type": "rect", "x": 0, "y": 0, "w": 85.6, "h": 14,
         "fill": "#1a2744", "type_color": False},
        # Akzent-Streifen (folgt dem Ausweis-Typ)
        {"type": "rect", "x": 0, "y": 14, "w": 85.6, "h": 1.2,
         "fill": "#cc2222", "type_color": True},

        # Header-Text
        {"type": "text", "x": 4, "y": 4, "w": 60,
         "value": "{{organisation}}", "font_size": 9, "weight": "bold",
         "color": "#ffffff", "align": "left"},
        {"type": "text", "x": 4, "y": 9, "w": 60,
         "value": "DIENSTAUSWEIS", "font_size": 6, "weight": "normal",
         "color": "#cbd5e1", "align": "left"},

        # Foto rechts
        {"type": "photo", "x": 60, "y": 18, "w": 22, "h": 30,
         "border_color": "#1a2744", "border_width": 0.4},

        # Personendaten
        {"type": "text", "x": 4, "y": 19, "w": 54,
         "value": "{{vorname}} {{nachname}}", "font_size": 11, "weight": "bold",
         "color": "#000000", "align": "left"},

        {"type": "text", "x": 4, "y": 27, "w": 54,
         "value": "{{dienstgrad}}", "font_size": 8, "weight": "normal",
         "color": "#334155", "align": "left"},

        {"type": "text", "x": 4, "y": 35, "w": 30,
         "value": "Pers.-Nr.", "font_size": 5, "weight": "normal",
         "color": "#64748b", "align": "left"},
        {"type": "text", "x": 4, "y": 38, "w": 30,
         "value": "{{dienstnummer}}", "font_size": 8, "weight": "bold",
         "color": "#000000", "align": "left"},

        {"type": "text", "x": 32, "y": 35, "w": 28,
         "value": "Gültig bis", "font_size": 5, "weight": "normal",
         "color": "#64748b", "align": "left"},
        {"type": "text", "x": 32, "y": 38, "w": 28,
         "value": "{{gueltig_bis}}", "font_size": 8, "weight": "bold",
         "color": "#000000", "align": "left"},

        # Footer-Streifen mit Ausweisnummer
        {"type": "rect", "x": 0, "y": 49, "w": 85.6, "h": 5,
         "fill": "#1a2744", "type_color": False},
        {"type": "text", "x": 4, "y": 50.5, "w": 81.6,
         "value": "Ausweis-Nr.: {{ausweisnummer}}", "font_size": 5.5,
         "weight": "normal", "color": "#ffffff", "align": "left"},
    ]


def _navy_landscape_back() -> list[dict]:
    return [
        {"type": "rect", "x": 0, "y": 0, "w": 85.6, "h": 6,
         "fill": "#1a2744", "type_color": False},
        {"type": "text", "x": 4, "y": 1.5, "w": 81.6,
         "value": "Eigentum von: {{organisation}}", "font_size": 5.5,
         "weight": "bold", "color": "#ffffff", "align": "left"},

        {"type": "text", "x": 4, "y": 10, "w": 77.6,
         "value": "Dieser Dienstausweis ist Eigentum der ausstellenden Stelle.",
         "font_size": 6, "weight": "bold", "color": "#000000", "align": "left"},

        {"type": "text", "x": 4, "y": 16, "w": 77.6,
         "value": "Bei Verlust oder Beschädigung umgehend melden. Mit Beendigung des Dienstes ist der Ausweis zurückzugeben.",
         "font_size": 5, "weight": "normal", "color": "#334155", "align": "left"},

        {"type": "text", "x": 4, "y": 38, "w": 77.6,
         "value": "Ausgestellt am: {{ausgestellt_am}}", "font_size": 5.5,
         "weight": "normal", "color": "#475569", "align": "left"},
        {"type": "text", "x": 4, "y": 42, "w": 77.6,
         "value": "Ausweis-Nr.: {{ausweisnummer}}", "font_size": 5.5,
         "weight": "normal", "color": "#475569", "align": "left"},
    ]


def _light_landscape_front() -> list[dict]:
    return [
        # Heller Hintergrund mit dünnem Border-Effekt (oben/unten)
        {"type": "rect", "x": 0, "y": 0, "w": 85.6, "h": 0.6,
         "fill": "#000000", "type_color": False},
        {"type": "rect", "x": 0, "y": 53.4, "w": 85.6, "h": 0.6,
         "fill": "#000000", "type_color": False},

        # Akzentbalken links (Ausweis-Typ-Farbe)
        {"type": "rect", "x": 0, "y": 0.6, "w": 2.5, "h": 52.8,
         "fill": "#cc2222", "type_color": True},

        # Header
        {"type": "text", "x": 6, "y": 4, "w": 60,
         "value": "{{organisation}}", "font_size": 9, "weight": "bold",
         "color": "#000000", "align": "left"},
        {"type": "text", "x": 6, "y": 9, "w": 60,
         "value": "Dienstausweis", "font_size": 6, "weight": "normal",
         "color": "#64748b", "align": "left"},

        # Foto rechts
        {"type": "photo", "x": 60, "y": 16, "w": 22, "h": 30,
         "border_color": "#94a3b8", "border_width": 0.3},

        # Daten
        {"type": "text", "x": 6, "y": 17, "w": 52,
         "value": "{{vorname}} {{nachname}}", "font_size": 11, "weight": "bold",
         "color": "#000000", "align": "left"},
        {"type": "text", "x": 6, "y": 25, "w": 52,
         "value": "{{dienstgrad}}", "font_size": 8, "weight": "normal",
         "color": "#475569", "align": "left"},

        {"type": "text", "x": 6, "y": 34, "w": 24,
         "value": "Pers.-Nr.", "font_size": 5, "weight": "normal",
         "color": "#94a3b8", "align": "left"},
        {"type": "text", "x": 6, "y": 37, "w": 24,
         "value": "{{dienstnummer}}", "font_size": 8, "weight": "bold",
         "color": "#000000", "align": "left"},

        {"type": "text", "x": 32, "y": 34, "w": 26,
         "value": "Gültig bis", "font_size": 5, "weight": "normal",
         "color": "#94a3b8", "align": "left"},
        {"type": "text", "x": 32, "y": 37, "w": 26,
         "value": "{{gueltig_bis}}", "font_size": 8, "weight": "bold",
         "color": "#000000", "align": "left"},

        {"type": "text", "x": 6, "y": 47, "w": 76,
         "value": "Ausweis-Nr.: {{ausweisnummer}}", "font_size": 5,
         "weight": "normal", "color": "#94a3b8", "align": "left"},
    ]


def _light_landscape_back() -> list[dict]:
    return [
        {"type": "rect", "x": 0, "y": 0, "w": 85.6, "h": 0.6,
         "fill": "#000000", "type_color": False},

        {"type": "text", "x": 4, "y": 6, "w": 77.6,
         "value": "{{organisation}}", "font_size": 7, "weight": "bold",
         "color": "#000000", "align": "left"},

        {"type": "text", "x": 4, "y": 14, "w": 77.6,
         "value": "Dieser Dienstausweis ist Eigentum der ausstellenden Stelle.",
         "font_size": 5.5, "weight": "bold", "color": "#000000", "align": "left"},
        {"type": "text", "x": 4, "y": 19, "w": 77.6,
         "value": "Bei Verlust oder Beschädigung umgehend melden. Mit Beendigung des Dienstes ist der Ausweis zurückzugeben.",
         "font_size": 5, "weight": "normal", "color": "#334155", "align": "left"},

        {"type": "text", "x": 4, "y": 36, "w": 77.6,
         "value": "Ausgestellt am: {{ausgestellt_am}}", "font_size": 5.5,
         "weight": "normal", "color": "#475569", "align": "left"},
        {"type": "text", "x": 4, "y": 40, "w": 77.6,
         "value": "Ausweis-Nr.: {{ausweisnummer}}", "font_size": 5.5,
         "weight": "normal", "color": "#475569", "align": "left"},

        {"type": "rect", "x": 0, "y": 53.4, "w": 85.6, "h": 0.6,
         "fill": "#000000", "type_color": False},
    ]


def _portrait_front() -> list[dict]:
    return [
        # Top-Header
        {"type": "rect", "x": 0, "y": 0, "w": 54, "h": 14,
         "fill": "#1a2744", "type_color": False},
        {"type": "rect", "x": 0, "y": 14, "w": 54, "h": 1.2,
         "fill": "#cc2222", "type_color": True},
        {"type": "text", "x": 3, "y": 3, "w": 48,
         "value": "{{organisation}}", "font_size": 8, "weight": "bold",
         "color": "#ffffff", "align": "left"},
        {"type": "text", "x": 3, "y": 8, "w": 48,
         "value": "DIENSTAUSWEIS", "font_size": 5, "weight": "normal",
         "color": "#cbd5e1", "align": "left"},

        # Foto mittig
        {"type": "photo", "x": 14.5, "y": 19, "w": 25, "h": 33,
         "border_color": "#1a2744", "border_width": 0.4},

        # Daten unten
        {"type": "text", "x": 3, "y": 55, "w": 48,
         "value": "{{vorname}} {{nachname}}", "font_size": 10, "weight": "bold",
         "color": "#000000", "align": "center"},
        {"type": "text", "x": 3, "y": 62, "w": 48,
         "value": "{{dienstgrad}}", "font_size": 7, "weight": "normal",
         "color": "#475569", "align": "center"},

        {"type": "text", "x": 3, "y": 70, "w": 24,
         "value": "Pers.-Nr.", "font_size": 4.5, "weight": "normal",
         "color": "#64748b", "align": "left"},
        {"type": "text", "x": 3, "y": 73, "w": 24,
         "value": "{{dienstnummer}}", "font_size": 7, "weight": "bold",
         "color": "#000000", "align": "left"},

        {"type": "text", "x": 27, "y": 70, "w": 24,
         "value": "Gültig bis", "font_size": 4.5, "weight": "normal",
         "color": "#64748b", "align": "left"},
        {"type": "text", "x": 27, "y": 73, "w": 24,
         "value": "{{gueltig_bis}}", "font_size": 7, "weight": "bold",
         "color": "#000000", "align": "left"},

        {"type": "rect", "x": 0, "y": 80.6, "w": 54, "h": 5,
         "fill": "#1a2744", "type_color": False},
        {"type": "text", "x": 3, "y": 82, "w": 48,
         "value": "Nr.: {{ausweisnummer}}", "font_size": 5,
         "weight": "normal", "color": "#ffffff", "align": "left"},
    ]


def _portrait_back() -> list[dict]:
    return [
        {"type": "rect", "x": 0, "y": 0, "w": 54, "h": 6,
         "fill": "#1a2744", "type_color": False},
        {"type": "text", "x": 3, "y": 1.5, "w": 48,
         "value": "{{organisation}}", "font_size": 5.5, "weight": "bold",
         "color": "#ffffff", "align": "left"},

        {"type": "text", "x": 3, "y": 11, "w": 48,
         "value": "Dieser Dienstausweis ist Eigentum der ausstellenden Stelle.",
         "font_size": 5, "weight": "bold", "color": "#000000", "align": "left"},
        {"type": "text", "x": 3, "y": 19, "w": 48,
         "value": "Bei Verlust oder Beschädigung umgehend melden. Mit Beendigung des Dienstes ist der Ausweis zurückzugeben.",
         "font_size": 4.5, "weight": "normal", "color": "#334155", "align": "left"},

        {"type": "text", "x": 3, "y": 70, "w": 48,
         "value": "Ausgestellt: {{ausgestellt_am}}", "font_size": 5,
         "weight": "normal", "color": "#475569", "align": "left"},
        {"type": "text", "x": 3, "y": 74, "w": 48,
         "value": "Nr.: {{ausweisnummer}}", "font_size": 5,
         "weight": "normal", "color": "#475569", "align": "left"},
    ]


# ----------------------------------------------------------------------------
# System-Template-Definitionen
# ----------------------------------------------------------------------------


SYSTEM_TEMPLATES: list[dict] = [
    {
        'name': 'Standard Navy (Querformat)',
        'description': (
            'Klassischer Dienstausweis im Querformat mit dunkelblauem '
            'Header und farbigem Akzent für den Ausweis-Typ.'
        ),
        'is_portrait': False,
        'is_default': True,
        'front_layout': _navy_landscape_front(),
        'back_layout': _navy_landscape_back(),
    },
    {
        'name': 'Hell Klassisch (Querformat)',
        'description': (
            'Heller Dienstausweis mit dünnem Rahmen und linkem Akzentbalken '
            'für den Ausweis-Typ.'
        ),
        'is_portrait': False,
        'is_default': False,
        'front_layout': _light_landscape_front(),
        'back_layout': _light_landscape_back(),
    },
    {
        'name': 'Modern (Hochformat)',
        'description': (
            'Hochformat mit Foto im Zentrum, dunkelblauem Header und Footer.'
        ),
        'is_portrait': True,
        'is_default': False,
        'front_layout': _portrait_front(),
        'back_layout': _portrait_back(),
    },
]


# ----------------------------------------------------------------------------
# Seed-Funktion
# ----------------------------------------------------------------------------


def _system_actor():
    """Lädt einen Audit-Aktor für System-Operationen (Superuser bevorzugt)."""
    return (
        User.objects.filter(is_superuser=True).order_by('pk').first()
        or User.objects.order_by('pk').first()
    )


@transaction.atomic
def ensure_system_templates(actor=None) -> int:
    """
    Legt System-Templates idempotent an oder überschreibt sie.
    Nutzer-Anpassungen würden verloren gehen — UI verbietet das.
    """
    actor = actor or _system_actor()
    if actor is None:
        # Ohne irgendeinen User können wir AuditedModel nicht speichern.
        # Aufrufer kann das ignorieren oder nochmal aufrufen, sobald ein
        # User existiert.
        return 0

    count = 0
    for spec in SYSTEM_TEMPLATES:
        defaults = {
            'description': spec['description'],
            'is_portrait': spec['is_portrait'],
            'front_layout': spec['front_layout'],
            'back_layout': spec['back_layout'],
            'is_system': True,
            'is_default': spec.get('is_default', False),
            'is_active': True,
            'updated_by': actor,
        }
        obj, created = IdCardTemplate.objects.get_or_create(
            name=spec['name'],
            defaults={**defaults, 'created_by': actor},
        )
        if not created:
            for field, value in defaults.items():
                setattr(obj, field, value)
            obj.save()
        count += 1

    # Genau ein Default-Template pro System.
    default_qs = IdCardTemplate.objects.filter(is_default=True)
    if default_qs.count() > 1:
        keep = default_qs.filter(is_system=True).order_by('pk').first()
        if keep:
            default_qs.exclude(pk=keep.pk).update(is_default=False)

    return count
