"""
Stellt alle vorhandenen Dienstausweis-Nummern auf das neue Format um:
zufällige, global eindeutige 6-stellige Nummer (100000–999999).

Nicht umkehrbar — die alten <STATION>-<JAHR>-<LFD>-Nummern lassen sich
nicht rekonstruieren.
"""

import secrets

from django.db import migrations


CARD_NUMBER_MIN = 100000
CARD_NUMBER_MAX = 999999


def renumber(apps, schema_editor):
    IdCard = apps.get_model('idcards', 'IdCard')
    cards = list(IdCard.objects.all().order_by('pk'))
    if not cards:
        return

    span = CARD_NUMBER_MAX - CARD_NUMBER_MIN + 1
    pool: set[int] = set()
    while len(pool) < len(cards):
        pool.add(CARD_NUMBER_MIN + secrets.randbelow(span))

    # Zweistufig zuweisen: erst alle auf temporäre, garantiert kollisionsfreie
    # Werte (negativer pk-Präfix), damit der UNIQUE-Constraint beim Umsetzen
    # nicht greift, falls eine neue Nummer zufällig einer alten gleicht.
    for card in cards:
        card.card_number = f"__tmp_{card.pk}"
        card.save(update_fields=['card_number'])

    for card, num in zip(cards, pool):
        card.card_number = str(num)
        card.save(update_fields=['card_number'])


def noop(apps, schema_editor):
    # Alte Nummern sind nicht wiederherstellbar.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('idcards', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(renumber, noop),
    ]
