"""
Migration 0012: Remove old vehicle FK fields from InfoMonitor.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0011_migrate_vehicle_data'),
    ]

    operations = [
        migrations.RemoveField(model_name='infomonitor', name='fahrzeug_ad_1'),
        migrations.RemoveField(model_name='infomonitor', name='fahrzeug_ad_2'),
        migrations.RemoveField(model_name='infomonitor', name='fahrzeug_ad_3'),
        migrations.RemoveField(model_name='infomonitor', name='ersetzt_mit_1'),
        migrations.RemoveField(model_name='infomonitor', name='ersetzt_mit_2'),
        migrations.RemoveField(model_name='infomonitor', name='ersetzt_mit_3'),
    ]
