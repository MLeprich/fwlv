# Generated manually
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0012_rename_item_to_device'),
    ]

    operations = [
        # Remove the assignment ForeignKey
        migrations.RemoveField(
            model_name='inspectionrecord',
            name='assignment',
        ),
        # Add device ForeignKey
        migrations.AddField(
            model_name='inspectionrecord',
            name='device',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='inspection_records',
                to='equipment.equipmentdeviceinstance',
                verbose_name='Gerät'
            ),
            preserve_default=False,
        ),
        # Add inspection_type ForeignKey
        migrations.AddField(
            model_name='inspectionrecord',
            name='inspection_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='inspection_records',
                to='equipment.inspectiontype',
                verbose_name='Prüfungsart'
            ),
            preserve_default=False,
        ),
    ]
