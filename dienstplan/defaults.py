"""
Vorbelegung der Dienstcodes (aus dem ersten Export der Fachabteilung Führungsdienst
abgeleitet: je Tag genau ein A1, A2, B, C-Dienst und Lagedienst).
F, FC, HB, L0, A2E und DV sind vom Fachbereich bestätigt (16.09.2026), die übrigen
Einträge tragen verified=False und sind in der Code-Tabelle zu prüfen.
"""

#: Vom Fachbereich bestätigte Bedeutungen (werden mit verified=True angelegt)
CONFIRMED = {'F', 'FC', 'HB', 'L0', 'A2E', 'DV'}

DEFAULT_CODES = [
    # code, label, kind, function, color, show_on_monitor, sort_order
    ('A1', 'A1-Dienst', 'duty', 'a1', 'red', True, 10),
    ('A2', 'A2-Dienst', 'duty', 'a2', 'orange', True, 11),
    ('A2E', 'Ersatz A-Dienst (A2)', 'duty', 'a2e', 'orange', True, 12),
    ('B', 'B-Dienst', 'duty', 'b', 'purple', True, 20),
    ('CT', 'C-Dienst (Wochentag)', 'duty', 'c', 'blue', True, 30),
    ('CTF', 'C-Dienst (Freitag)', 'duty', 'c', 'blue', True, 31),
    ('CW', 'C-Dienst (Wochenende)', 'duty', 'c', 'blue', True, 32),
    ('LD', 'Lagedienst', 'duty', 'lagedienst', 'green', True, 40),
    ('LDS', 'Lagedienst (Wochenende/Feiertag)', 'duty', 'lagedienst', 'green', True, 41),
    ('BÜ', 'Büro', 'office', '', 'gray', False, 50),
    ('BÜF', 'Büro (Freitag)', 'office', '', 'gray', False, 51),
    ('HB', 'Home Office', 'office', '', 'gray', False, 60),
    ('DV', 'Dienstvertretung', 'duty', '', 'gray', False, 61),
    ('L', 'Lehrgang', 'training', '', 'yellow', False, 70),
    ('L0', 'Frei nach Lehrgang', 'free', '', 'gray', False, 71),
    ('F', 'Frei', 'free', '', 'gray', False, 72),
    ('FC', 'Frei C-Dienst', 'free', '', 'gray', False, 73),
    ('U', 'Urlaub', 'absence', '', 'yellow', False, 80),
    ('K', 'Krank', 'absence', '', 'red', False, 81),
    ('EZ', 'Elternzeit', 'absence', '', 'yellow', False, 82),
    ('-', 'Frei', 'free', '', 'gray', False, 90),
]


def ensure_default_codes(DutyCode):
    """
    Fehlende Standardcodes anlegen. Bestätigte Codes (CONFIRMED) werden auch bei
    bestehenden, noch ungeprüften Einträgen auf die bestätigte Bedeutung gesetzt;
    vom Nutzer bereits geprüfte Einträge bleiben unverändert.
    """
    created = 0
    for code, label, kind, function, color, show, order in DEFAULT_CODES:
        values = {'label': label, 'kind': kind, 'function': function, 'color': color,
                  'show_on_monitor': show, 'sort_order': order, 'verified': code in CONFIRMED}
        obj, was_created = DutyCode.objects.get_or_create(code=code, defaults=values)
        created += was_created
        if not was_created and code in CONFIRMED and not obj.verified:
            for key, value in values.items():
                setattr(obj, key, value)
            obj.save()
    return created
