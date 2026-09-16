"""
Vorbelegung der Dienstcodes (aus dem ersten Export der Fachabteilung Führungsdienst
abgeleitet: je Tag genau ein A1, A2, B, C-Dienst und Lagedienst). Alle Einträge
tragen verified=False und sind in der Code-Tabelle zu prüfen.
"""

DEFAULT_CODES = [
    # code, label, kind, function, color, show_on_monitor, sort_order
    ('A1', 'A1-Dienst', 'duty', 'a1', 'red', True, 10),
    ('A2', 'A2-Dienst', 'duty', 'a2', 'orange', True, 11),
    ('A2E', 'A2-Dienst (Einweisung)', 'duty', '', 'orange', False, 12),
    ('B', 'B-Dienst', 'duty', 'b', 'purple', True, 20),
    ('CT', 'C-Dienst (Wochentag)', 'duty', 'c', 'blue', True, 30),
    ('CTF', 'C-Dienst (Freitag)', 'duty', 'c', 'blue', True, 31),
    ('CW', 'C-Dienst (Wochenende)', 'duty', 'c', 'blue', True, 32),
    ('LD', 'Lagedienst', 'duty', 'lagedienst', 'green', True, 40),
    ('LDS', 'Lagedienst (Wochenende/Feiertag)', 'duty', 'lagedienst', 'green', True, 41),
    ('BÜ', 'Büro', 'office', '', 'gray', False, 50),
    ('BÜF', 'Büro (Freitag)', 'office', '', 'gray', False, 51),
    ('HB', 'HB', 'other', '', 'gray', False, 60),
    ('DV', 'DV', 'other', '', 'gray', False, 61),
    ('L', 'Lehrgang', 'training', '', 'yellow', False, 70),
    ('L0', 'L0', 'training', '', 'yellow', False, 71),
    ('F', 'F', 'other', '', 'gray', False, 72),
    ('FC', 'FC', 'other', '', 'gray', False, 73),
    ('U', 'Urlaub', 'absence', '', 'yellow', False, 80),
    ('K', 'Krank', 'absence', '', 'red', False, 81),
    ('EZ', 'Elternzeit', 'absence', '', 'yellow', False, 82),
    ('-', 'Frei', 'free', '', 'gray', False, 90),
]


def ensure_default_codes(DutyCode):
    """Fehlende Standardcodes anlegen; bestehende bleiben unverändert."""
    created = 0
    for code, label, kind, function, color, show, order in DEFAULT_CODES:
        _, was_created = DutyCode.objects.get_or_create(code=code, defaults={
            'label': label, 'kind': kind, 'function': function, 'color': color,
            'show_on_monitor': show, 'sort_order': order, 'verified': False,
        })
        created += was_created
    return created
