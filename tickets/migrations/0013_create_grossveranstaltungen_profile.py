"""
Datenmigration: Erstellt das MonitorProfile "Großveranstaltungen"
für die Digitale Mappe Dashboard-Funktion.
"""

from django.db import migrations


def create_grossveranstaltungen_profile(apps, schema_editor):
    MonitorProfile = apps.get_model('info_monitors', 'MonitorProfile')
    User = apps.get_model('core', 'User')

    # Ersten Superuser als created_by/updated_by verwenden
    admin_user = User.objects.filter(is_superuser=True).order_by('pk').first()
    if not admin_user:
        admin_user = User.objects.order_by('pk').first()
    if not admin_user:
        return  # Keine User vorhanden, Profil wird zur Laufzeit erstellt

    if not MonitorProfile.objects.filter(name='Großveranstaltungen').exists():
        MonitorProfile.objects.create(
            name='Großveranstaltungen',
            description='Dashboards für Großveranstaltungen (Digitale Mappe)',
            icon='🎪',
            color='#dc2626',
            is_active=True,
            is_default=False,
            display_order=99,
            created_by=admin_user,
            updated_by=admin_user,
        )


def remove_grossveranstaltungen_profile(apps, schema_editor):
    MonitorProfile = apps.get_model('info_monitors', 'MonitorProfile')
    MonitorProfile.objects.filter(name='Großveranstaltungen').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0012_remove_old_vehicle_fields'),
        ('info_monitors', '0004_widget_pdf_file'),
        ('core', '0020_rename_civil_protection_setting'),
    ]

    operations = [
        migrations.RunPython(
            create_grossveranstaltungen_profile,
            remove_grossveranstaltungen_profile,
        ),
    ]
