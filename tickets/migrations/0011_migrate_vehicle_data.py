"""
Migration 0011: Data migration – move old fahrzeug_ad_1/2/3 + ersetzt_mit_1/2/3
into new InfoMonitorVehicle entries.
"""
from django.db import migrations


def forwards(apps, schema_editor):
    InfoMonitor = apps.get_model('tickets', 'InfoMonitor')
    InfoMonitorVehicle = apps.get_model('tickets', 'InfoMonitorVehicle')

    for monitor in InfoMonitor.objects.all():
        slots = [
            (monitor.fahrzeug_ad_1_id, monitor.ersetzt_mit_1_id),
            (monitor.fahrzeug_ad_2_id, monitor.ersetzt_mit_2_id),
            (monitor.fahrzeug_ad_3_id, monitor.ersetzt_mit_3_id),
        ]
        for pos, (ad_id, ersetzt_id) in enumerate(slots):
            if ad_id or ersetzt_id:
                InfoMonitorVehicle.objects.create(
                    monitor=monitor,
                    fahrzeug_ad_id=ad_id,
                    ersetzt_mit_id=ersetzt_id,
                    position=pos,
                )


def backwards(apps, schema_editor):
    InfoMonitor = apps.get_model('tickets', 'InfoMonitor')
    InfoMonitorVehicle = apps.get_model('tickets', 'InfoMonitorVehicle')

    for monitor in InfoMonitor.objects.all():
        vehicles = list(InfoMonitorVehicle.objects.filter(monitor=monitor).order_by('position')[:3])
        field_map = [
            ('fahrzeug_ad_1_id', 'ersetzt_mit_1_id'),
            ('fahrzeug_ad_2_id', 'ersetzt_mit_2_id'),
            ('fahrzeug_ad_3_id', 'ersetzt_mit_3_id'),
        ]
        for i, (ad_field, ersetzt_field) in enumerate(field_map):
            if i < len(vehicles):
                setattr(monitor, ad_field, vehicles[i].fahrzeug_ad_id)
                setattr(monitor, ersetzt_field, vehicles[i].ersetzt_mit_id)
            else:
                setattr(monitor, ad_field, None)
                setattr(monitor, ersetzt_field, None)
        monitor.save()


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0010_infomonitorvehicle_laufband'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
