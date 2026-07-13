"""
Hebt die Personenzuordnung auf Lagerartikeln (Mengenposten) auf.

Bisher stempelte jeder Warenausgang die Person auf den ganzen Artikel – so galt
z.B. "Weste XL, 39 Stück" als komplett an eine Person zugeordnet, obwohl nur ein
Stück ausgegeben war. Zudem überschrieb jede weitere Ausgabe die vorherige Person.

Wer wieviel offen hat, wird jetzt aus den Lagerbewegungen abgeleitet
(clothing/assignments.py). Die Werte hier sind damit redundant und irreführend.
Die Bewegungen bleiben unangetastet, es geht keine Information verloren.
"""
from django.db import migrations


def clear_person_assignment(apps, schema_editor):
    ClothingItem = apps.get_model('clothing', 'ClothingItem')
    ClothingItem.objects.filter(assigned_to__isnull=False).update(
        assigned_to=None,
        assignment_date=None,
        is_personal_issue=False,
    )


def noop(apps, schema_editor):
    """
    Nicht umkehrbar – die Zuordnung lässt sich aber jederzeit aus den
    Lagerbewegungen rekonstruieren, dort liegt sie vollständig vor.
    """


class Migration(migrations.Migration):

    dependencies = [
        ('clothing', '0008_add_product_type_model'),
    ]

    operations = [
        migrations.RunPython(clear_person_assignment, noop),
    ]
