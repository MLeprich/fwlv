"""
Migration: Bereitschafts-Kategorien (9 Werte) zu Pools (3 Werte) konsolidieren.

Mapping:
    a1_dienst, a2_dienst, b_dienst, c_dienst, lagedienst -> fuehrungsdienst
    lna                                                  -> aerztliche_leitung
    ordnungsamt, gesundheitsamt, veterinaeramt           -> stadt

Doppelte (Name, Pool)-Kombinationen werden zusammengeführt: der erste Eintrag
behält die Telefonnummer, weitere Einträge werden gelöscht.
"""
from django.db import migrations, models


KATEGORIE_TO_POOL = {
    'a1_dienst': 'fuehrungsdienst',
    'a2_dienst': 'fuehrungsdienst',
    'b_dienst': 'fuehrungsdienst',
    'c_dienst': 'fuehrungsdienst',
    'lagedienst': 'fuehrungsdienst',
    'lna': 'aerztliche_leitung',
    'ordnungsamt': 'stadt',
    'gesundheitsamt': 'stadt',
    'veterinaeramt': 'stadt',
}


def kategorie_to_pool(apps, schema_editor):
    BP = apps.get_model('tickets', 'BereitschaftPerson')
    seen = {}  # (name_lower, pool) -> id of kept row
    for p in BP.objects.all().order_by('id'):
        new_pool = KATEGORIE_TO_POOL.get(p.kategorie, 'fuehrungsdienst')
        key = (p.name.strip().lower(), new_pool)
        if key in seen:
            # Dublette: ggf. Telefon des bestehenden Eintrags ergänzen
            kept = BP.objects.get(pk=seen[key])
            if p.phone and not kept.phone:
                kept.phone = p.phone
                kept.save(update_fields=['phone'])
            p.delete()
        else:
            p.pool = new_pool
            p.save(update_fields=['pool'])
            seen[key] = p.id


def pool_to_kategorie(apps, schema_editor):
    """Reverse: setzt kategorie auf einen Default-Wert je Pool. Echte
    Rückwärtsmigration ist verlustbehaftet (Pool -> 1 von mehreren Kategorien).
    """
    BP = apps.get_model('tickets', 'BereitschaftPerson')
    fallback = {
        'fuehrungsdienst': 'c_dienst',
        'aerztliche_leitung': 'lna',
        'stadt': 'ordnungsamt',
    }
    for p in BP.objects.all():
        p.kategorie = fallback.get(p.pool, 'c_dienst')
        p.save(update_fields=['kategorie'])


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0027_sonstiges_highlighted'),
    ]

    operations = [
        migrations.AddField(
            model_name='bereitschaftperson',
            name='pool',
            field=models.CharField(
                choices=[
                    ('fuehrungsdienst', 'Führungsdienst'),
                    ('aerztliche_leitung', 'Ärztliche Leitung'),
                    ('stadt', 'Stadt'),
                ],
                default='fuehrungsdienst',
                max_length=30,
                verbose_name='Pool',
            ),
        ),
        migrations.RunPython(kategorie_to_pool, pool_to_kategorie),
        migrations.RemoveField(
            model_name='bereitschaftperson',
            name='kategorie',
        ),
    ]
