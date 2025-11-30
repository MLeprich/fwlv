# Generated manually for unifying on DivingDeviceInstance

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('diving', '0011_alter_divinginventorycheck_check_type'),
    ]

    operations = [
        # Step 1: Remove old constraints
        migrations.AlterUniqueTogether(
            name='divingserviceassignment',
            unique_together=set(),
        ),

        # Step 2: Add new device field (nullable temporarily)
        migrations.AddField(
            model_name='divingserviceassignment',
            name='device',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='service_assignments',
                to='diving.divingdeviceinstance',
                verbose_name='Geräte-Instanz'
            ),
        ),

        # Step 3: Remove old item field
        migrations.RemoveField(
            model_name='divingserviceassignment',
            name='item',
        ),

        # Step 4: Make device field required
        migrations.AlterField(
            model_name='divingserviceassignment',
            name='device',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='service_assignments',
                to='diving.divingdeviceinstance',
                verbose_name='Geräte-Instanz'
            ),
        ),

        # Step 5: Add new constraints
        migrations.AlterUniqueTogether(
            name='divingserviceassignment',
            unique_together={('device', 'service_type')},
        ),

        # Step 6: Update ordering
        migrations.AlterModelOptions(
            name='divingserviceassignment',
            options={
                'ordering': ['device', 'service_type'],
                'verbose_name': 'Wartungszuweisung',
                'verbose_name_plural': 'Wartungszuweisungen'
            },
        ),
    ]
