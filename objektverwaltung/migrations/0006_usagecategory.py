import django.db.models.deletion
from django.db import migrations, models

# Bisherige feste Nutzungsarten (Code, Bezeichnung) in Anzeigereihenfolge
STANDARD_USAGE_TYPES = [
    ('school', 'Schule'),
    ('kindergarten', 'Kindergarten / Kita'),
    ('hospital', 'Krankenhaus / Pflege'),
    ('assembly', 'Versammlungsstätte'),
    ('office', 'Verwaltung / Büro'),
    ('industry', 'Industrie / Gewerbe'),
    ('residential', 'Wohngebäude'),
    ('other', 'Sonstiges'),
]


def seed_categories(apps, schema_editor):
    UsageCategory = apps.get_model('objektverwaltung', 'UsageCategory')
    BuildingObject = apps.get_model('objektverwaltung', 'BuildingObject')

    by_code = {}
    for index, (code, name) in enumerate(STANDARD_USAGE_TYPES):
        category, _ = UsageCategory.objects.get_or_create(
            name=name, defaults={'sort_order': (index + 1) * 10},
        )
        by_code[code] = category

    # Sicherheitsnetz: unbekannte Codes aus Bestandsdaten als eigene Nutzungsart übernehmen
    for code in BuildingObject.objects.values_list('usage_type_code', flat=True).distinct():
        if code and code not in by_code:
            by_code[code], _ = UsageCategory.objects.get_or_create(name=code, defaults={'sort_order': 100})

    for code, category in by_code.items():
        BuildingObject.objects.filter(usage_type_code=code).update(usage_type=category)


def unseed_categories(apps, schema_editor):
    UsageCategory = apps.get_model('objektverwaltung', 'UsageCategory')
    BuildingObject = apps.get_model('objektverwaltung', 'BuildingObject')
    name_to_code = {name: code for code, name in STANDARD_USAGE_TYPES}
    for category in UsageCategory.objects.all():
        code = name_to_code.get(category.name, 'other')
        BuildingObject.objects.filter(usage_type=category).update(usage_type_code=code)


class Migration(migrations.Migration):

    dependencies = [
        ('objektverwaltung', '0005_buildingobject_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='UsageCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Wird in Listen und Auswahlfeldern angezeigt', max_length=100, unique=True, verbose_name='Bezeichnung')),
                ('sort_order', models.PositiveSmallIntegerField(default=0, help_text='Kleinere Werte stehen weiter oben', verbose_name='Reihenfolge')),
                ('is_active', models.BooleanField(default=True, help_text='Inaktive Nutzungsarten stehen für neue Objekte nicht mehr zur Auswahl; bestehende Objekte behalten sie', verbose_name='Aktiv')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Erstellt am')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Aktualisiert am')),
            ],
            options={
                'verbose_name': 'Nutzungsart',
                'verbose_name_plural': 'Nutzungsarten',
                'ordering': ['sort_order', 'name'],
            },
        ),
        migrations.RenameField(
            model_name='buildingobject',
            old_name='usage_type',
            new_name='usage_type_code',
        ),
        migrations.AddField(
            model_name='buildingobject',
            name='usage_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='buildings', to='objektverwaltung.usagecategory', verbose_name='Nutzungsart'),
        ),
        migrations.RunPython(seed_categories, unseed_categories),
        migrations.RemoveField(
            model_name='buildingobject',
            name='usage_type_code',
        ),
    ]
