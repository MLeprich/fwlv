"""
Migration 3/3: Remove old CharField, rename new FK to vehicle_type
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vehicles', '0009_migrate_vehicle_types'),
    ]

    operations = [
        # 1. Remove old CharField from Vehicle
        migrations.RemoveField(
            model_name='vehicle',
            name='vehicle_type',
        ),
        # 2. Rename new FK to vehicle_type on Vehicle
        migrations.RenameField(
            model_name='vehicle',
            old_name='vehicle_type_new',
            new_name='vehicle_type',
        ),
        # 3. Update FK properties on Vehicle (related_name, limit_choices_to)
        migrations.AlterField(
            model_name='vehicle',
            name='vehicle_type',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='vehicles',
                to='vehicles.vehicletype',
                verbose_name='Fahrzeugtyp',
                limit_choices_to={'is_active': True},
            ),
        ),
        # 4. Remove old CharField from VehicleModel
        migrations.RemoveField(
            model_name='vehiclemodel',
            name='vehicle_type',
        ),
        # 5. Rename new FK to vehicle_type on VehicleModel
        migrations.RenameField(
            model_name='vehiclemodel',
            old_name='vehicle_type_new',
            new_name='vehicle_type',
        ),
        # 6. Update FK properties on VehicleModel
        migrations.AlterField(
            model_name='vehiclemodel',
            name='vehicle_type',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='vehicle_models',
                to='vehicles.vehicletype',
                verbose_name='Standardtyp',
                help_text='Standard-Fahrzeugtyp für dieses Modell',
                limit_choices_to={'is_active': True},
            ),
        ),
    ]
