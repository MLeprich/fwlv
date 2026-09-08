"""
Nachweisarten als eigene Tabelle (statt fester Choices), damit weitere
Führerscheine (BOS, EGRED, …) im Modul selbst gepflegt werden können.

Die bisherigen Kürzel (a1_a3, a2, sts) bleiben in den Datensätzen erhalten und
werden als Startbestand in die neue Tabelle übernommen.
"""

from django.db import migrations, models

STANDARD_KINDS = [
    ('a1_a3', 'EU-Kompetenznachweis A1/A3', 5, 10),
    ('a2', 'EU-Fernpiloten-Zeugnis A2', 5, 20),
    ('sts', 'Standardszenarien STS-01/STS-02', 5, 30),
]


def seed_kinds(apps, schema_editor):
    DroneLicenseKind = apps.get_model('iuk', 'DroneLicenseKind')
    DroneLicense = apps.get_model('iuk', 'DroneLicense')
    Voucher = apps.get_model('iuk', 'Voucher')
    VoucherEvent = apps.get_model('iuk', 'VoucherEvent')

    for code, name, years, order in STANDARD_KINDS:
        DroneLicenseKind.objects.get_or_create(
            code=code,
            defaults={'name': name, 'validity_years': years, 'sort_order': order},
        )

    # Sicherheitsnetz: Kürzel aus Bestandsdaten, die nicht zum Standard gehören.
    used = set()
    used.update(DroneLicense.objects.values_list('license_type', flat=True))
    used.update(Voucher.objects.exclude(intended_use='').values_list('intended_use', flat=True))
    used.update(VoucherEvent.objects.exclude(license_type='').values_list('license_type', flat=True))
    for code in sorted(c for c in used if c):
        DroneLicenseKind.objects.get_or_create(
            code=code, defaults={'name': code, 'sort_order': 100},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('iuk', '0006_flightlog_postflight_results_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='DroneLicenseKind',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(help_text='Technischer Schlüssel, z.B. "bos" – wird aus der Bezeichnung gebildet und kann nachträglich nicht geändert werden', max_length=40, unique=True, verbose_name='Kürzel')),
                ('name', models.CharField(help_text='Wird in Listen und Auswahlfeldern angezeigt', max_length=150, unique=True, verbose_name='Bezeichnung')),
                ('description', models.TextField(blank=True, help_text='Optionaler Hinweis, z.B. Rechtsgrundlage oder ausstellende Stelle', verbose_name='Beschreibung')),
                ('validity_years', models.PositiveSmallIntegerField(blank=True, help_text='Belegt beim Anlegen das Ablaufdatum vor; leer lassen, wenn die Gültigkeit unterschiedlich oder unbegrenzt ist', null=True, verbose_name='Regelgültigkeit (Jahre)')),
                ('sort_order', models.PositiveSmallIntegerField(default=0, help_text='Kleinere Werte stehen weiter oben', verbose_name='Reihenfolge')),
                ('is_active', models.BooleanField(default=True, help_text='Inaktive Arten stehen für neue Einträge nicht mehr zur Auswahl; bestehende Einträge bleiben erhalten', verbose_name='Aktiv')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Erstellt am')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Aktualisiert am')),
            ],
            options={
                'verbose_name': 'Nachweisart',
                'verbose_name_plural': 'Nachweisarten',
                'ordering': ['sort_order', 'name'],
            },
        ),
        migrations.AlterField(
            model_name='dronelicense',
            name='license_type',
            field=models.CharField(db_index=True, help_text='Kürzel einer Nachweisart (siehe Nachweisarten)', max_length=40, verbose_name='Art des Nachweises'),
        ),
        migrations.AlterField(
            model_name='dronelicense',
            name='expiry_date',
            field=models.DateField(db_index=True, help_text='Vor Ablauf wird automatisch erinnert', verbose_name='Gültig bis'),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='intended_use',
            field=models.CharField(blank=True, help_text='Nachweis, für den der Gutschein eingesetzt werden soll', max_length=40, verbose_name='Für welchen Nachweis'),
        ),
        migrations.AlterField(
            model_name='voucherevent',
            name='license_type',
            field=models.CharField(blank=True, max_length=40, verbose_name='Für welchen Nachweis'),
        ),
        migrations.RunPython(seed_kinds, migrations.RunPython.noop),
    ]
