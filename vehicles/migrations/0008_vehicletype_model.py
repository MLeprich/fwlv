"""
Migration 1/3: Create VehicleType model and add temporary FK fields
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vehicles', '0007_remove_vehicle_manufacturer_model'),
    ]

    operations = [
        # 1. Create VehicleType model
        migrations.CreateModel(
            name='VehicleType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Bezeichnung')),
                ('code', models.SlugField(max_length=30, unique=True, verbose_name='Code', help_text='Interner Code (z.B. hlf20, dlk)')),
                ('description', models.TextField(blank=True, verbose_name='Beschreibung')),
                ('icon', models.CharField(blank=True, default='🚒', max_length=10, verbose_name='Icon')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Reihenfolge')),
                ('is_active', models.BooleanField(default=True, verbose_name='Aktiv')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Fahrzeugtyp',
                'verbose_name_plural': 'Fahrzeugtypen',
                'ordering': ['order', 'name'],
            },
        ),
        # 2. Add temporary FK field to Vehicle (vehicle_type_new)
        migrations.AddField(
            model_name='vehicle',
            name='vehicle_type_new',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='vehicles_new',
                to='vehicles.vehicletype',
                verbose_name='Fahrzeugtyp (neu)',
            ),
        ),
        # 3. Add temporary FK field to VehicleModel (vehicle_type_new)
        migrations.AddField(
            model_name='vehiclemodel',
            name='vehicle_type_new',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='vehicle_models_new',
                to='vehicles.vehicletype',
                verbose_name='Standardtyp (neu)',
            ),
        ),
    ]
