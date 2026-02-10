"""
Migration: Change ChecklistTemplate.vehicle_types from JSONField to M2M
"""

from django.db import migrations, models


def migrate_json_to_m2m(apps, schema_editor):
    """Convert JSONField vehicle_types codes to M2M relations"""
    ChecklistTemplate = apps.get_model('vehicle_handover', 'ChecklistTemplate')
    VehicleType = apps.get_model('vehicles', 'VehicleType')

    for template in ChecklistTemplate.objects.all():
        # Read old JSON data from the renamed field
        old_codes = template.vehicle_types_old or []
        if isinstance(old_codes, list):
            for code in old_codes:
                try:
                    vtype = VehicleType.objects.get(code=code)
                    template.vehicle_types.add(vtype)
                except VehicleType.DoesNotExist:
                    pass  # Skip unknown codes


def migrate_m2m_to_json(apps, schema_editor):
    """Reverse: Convert M2M relations back to JSON codes"""
    ChecklistTemplate = apps.get_model('vehicle_handover', 'ChecklistTemplate')

    for template in ChecklistTemplate.objects.all():
        codes = list(template.vehicle_types.values_list('code', flat=True))
        template.vehicle_types_old = codes
        template.save(update_fields=['vehicle_types_old'])


class Migration(migrations.Migration):

    dependencies = [
        ('vehicle_handover', '0006_add_custom_checklist'),
        ('vehicles', '0010_cleanup_vehicle_type'),
    ]

    operations = [
        # 1. Rename old JSONField to vehicle_types_old
        migrations.RenameField(
            model_name='checklisttemplate',
            old_name='vehicle_types',
            new_name='vehicle_types_old',
        ),
        # 2. Add new M2M field
        migrations.AddField(
            model_name='checklisttemplate',
            name='vehicle_types',
            field=models.ManyToManyField(
                blank=True,
                help_text='Fahrzeugtypen, für die dieses Template gilt',
                related_name='checklist_templates',
                to='vehicles.vehicletype',
                verbose_name='Fahrzeugtypen',
            ),
        ),
        # 3. Migrate data
        migrations.RunPython(migrate_json_to_m2m, migrate_m2m_to_json),
        # 4. Remove old JSON field
        migrations.RemoveField(
            model_name='checklisttemplate',
            name='vehicle_types_old',
        ),
    ]
