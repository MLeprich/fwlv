"""
Step 2: Data migration - Seed categories from old TextChoices + migrate existing Defects
"""

from django.db import migrations


SEED_CATEGORIES = [
    {
        'name': 'Fahrzeug',
        'icon': '\U0001F691',  # ambulance
        'color': 'blue',
        'app_label': 'vehicles',
        'model_name': 'vehicle',
        'sort_order': 10,
        'old_value': 'vehicle',
    },
    {
        'name': 'Raum / Standort',
        'icon': '\U0001F3E2',  # office building
        'color': 'gray',
        'app_label': 'locations',
        'model_name': 'location',
        'sort_order': 20,
        'old_value': 'location',
    },
    {
        'name': 'Ausrüstung & Geräte',
        'icon': '\U0001F527',  # wrench
        'color': 'amber',
        'app_label': 'equipment',
        'model_name': 'equipmentitem',
        'sort_order': 30,
        'old_value': 'equipment',
    },
    {
        'name': 'Bekleidung',
        'icon': '\U0001F9E5',  # coat
        'color': 'indigo',
        'app_label': 'clothing',
        'model_name': 'clothingitem',
        'sort_order': 40,
        'old_value': 'clothing',
    },
    {
        'name': 'Rettungsdienst / Medizin',
        'icon': '\U0001FA7A',  # stethoscope
        'color': 'red',
        'app_label': 'medical',
        'model_name': 'medicalitem',
        'sort_order': 50,
        'old_value': 'medical',
    },
    {
        'name': 'Verbrauchsmaterial',
        'icon': '\U0001F4E6',  # package
        'color': 'orange',
        'app_label': 'magazine',
        'model_name': 'magazineitem',
        'sort_order': 60,
        'old_value': 'magazine',
    },
    {
        'name': 'Werkstatt',
        'icon': '\U0001F6E0',  # hammer and wrench
        'color': 'yellow',
        'app_label': 'workshop',
        'model_name': 'workshopitem',
        'sort_order': 70,
        'old_value': 'workshop',
    },
    {
        'name': 'Höhenrettung',
        'icon': '\U0001FA82',  # parachute
        'color': 'teal',
        'app_label': 'height_rescue',
        'model_name': 'heightrescuedeviceinstance',
        'sort_order': 80,
        'old_value': 'height_rescue',
    },
    {
        'name': 'Taucher',
        'icon': '\U0001F93F',  # diving mask
        'color': 'cyan',
        'app_label': 'diving',
        'model_name': 'divingdeviceinstance',
        'sort_order': 90,
        'old_value': 'diving',
    },
    {
        'name': 'IT-Hardware',
        'icon': '\U0001F4BB',  # laptop
        'color': 'purple',
        'app_label': 'it_hardware',
        'model_name': 'ithardwareitem',
        'sort_order': 100,
        'old_value': 'it_hardware',
    },
    {
        'name': 'Sonstiges',
        'icon': '\u26a0\ufe0f',  # warning sign
        'color': '',
        'app_label': '',
        'model_name': '',
        'sort_order': 999,
        'old_value': 'other',
    },
]


def seed_categories_and_migrate(apps, schema_editor):
    DefectCategoryModel = apps.get_model('defect_management', 'DefectCategoryModel')
    Defect = apps.get_model('defect_management', 'Defect')

    # Build lookup: old_value -> new category instance
    old_to_new = {}
    for cat_data in SEED_CATEGORIES:
        old_value = cat_data.pop('old_value')
        category, _ = DefectCategoryModel.objects.get_or_create(
            name=cat_data['name'],
            defaults=cat_data,
        )
        old_to_new[old_value] = category

    # Migrate existing defects
    for defect in Defect.objects.all():
        new_cat = old_to_new.get(defect.category)
        if new_cat:
            defect.category_new = new_cat
            defect.save(update_fields=['category_new'])


def reverse_migration(apps, schema_editor):
    """Reverse: copy category_new back to old CharField"""
    DefectCategoryModel = apps.get_model('defect_management', 'DefectCategoryModel')
    Defect = apps.get_model('defect_management', 'Defect')

    # Build reverse lookup: category name -> old_value
    name_to_old = {}
    for cat_data in SEED_CATEGORIES:
        name_to_old[cat_data['name']] = cat_data['old_value']

    for defect in Defect.objects.filter(category_new__isnull=False):
        old_val = name_to_old.get(defect.category_new.name, 'other')
        defect.category = old_val
        defect.save(update_fields=['category'])


class Migration(migrations.Migration):

    dependencies = [
        ('defect_management', '0002_defectcategorymodel_defect_category_new'),
    ]

    operations = [
        migrations.RunPython(seed_categories_and_migrate, reverse_migration),
    ]
