# Generated manually for unifying DivingServiceLog on DivingDeviceInstance

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('diving', '0013_alter_divingserviceassignment_options'),
    ]

    operations = [
        # Step 1: Remove old index
        migrations.RemoveIndex(
            model_name='divingservicelog',
            name='diving_divi_item_id_0ab652_idx',
        ),

        # Step 2: Add new device field (nullable temporarily)
        migrations.AddField(
            model_name='divingservicelog',
            name='device',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='service_logs',
                to='diving.divingdeviceinstance',
                verbose_name='Geräte-Instanz'
            ),
        ),

        # Step 3: Remove old item field
        migrations.RemoveField(
            model_name='divingservicelog',
            name='item',
        ),

        # Step 4: Make device field required
        migrations.AlterField(
            model_name='divingservicelog',
            name='device',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='service_logs',
                to='diving.divingdeviceinstance',
                verbose_name='Geräte-Instanz'
            ),
        ),

        # Step 5: Add new index
        migrations.AddIndex(
            model_name='divingservicelog',
            index=models.Index(fields=['device', 'service_date'], name='diving_divi_device__8a2c1f_idx'),
        ),
    ]
