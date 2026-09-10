# Startwerte für die PSV-Prüfarten nach § 2 PrüfVO NRW (wiederkehrend alle drei
# Jahre). Die Liste ist unter „PSV-Prüfarten“ frei änderbar.

from django.db import migrations

PRUEFARTEN = [
    'Brandmelde- und Alarmierungsanlagen',
    'Rauchabzugsanlagen / Rauchabzugsgeräte (RWA)',
    'Rauchschutz-Druckanlagen (RDA)',
    'Lüftungsanlagen',
    'CO-Warnanlagen',
    'Selbsttätige Feuerlöschanlagen (Sprinkler, Sprühwasser, Gas)',
    'Nichtselbsttätige Feuerlöschanlagen (nasse Steigleitungen)',
    'Sicherheitsstromversorgung / Sicherheitsbeleuchtung',
]


def create_types(apps, schema_editor):
    PSVInspectionType = apps.get_model('objektverwaltung', 'PSVInspectionType')
    for index, name in enumerate(PRUEFARTEN, start=1):
        PSVInspectionType.objects.get_or_create(
            name=name, defaults={'sort_order': index * 10, 'interval_months': 36, 'warning_days': 90},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('objektverwaltung', '0007_brandverhuetungsschau'),
    ]

    operations = [
        migrations.RunPython(create_types, migrations.RunPython.noop),
    ]
