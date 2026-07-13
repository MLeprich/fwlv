"""
Startpunkt der Funkrufnamen-Historie setzen.

Für jedes Fahrzeug, das heute einen Funkrufnamen trägt, wird eine offene Zuordnung
angelegt. Ab wann es ihn hat, wissen wir nicht mehr – wir nehmen das Anlagedatum des
Fahrzeugs. Ab hier ist die Historie lückenlos.
"""
from django.db import migrations
from django.utils import timezone


def seed_history(apps, schema_editor):
    Vehicle = apps.get_model('vehicles', 'Vehicle')
    CallSignAssignment = apps.get_model('vehicles', 'CallSignAssignment')

    heute = timezone.localdate()
    for vehicle in Vehicle.objects.exclude(call_sign=''):
        if CallSignAssignment.objects.filter(vehicle=vehicle, valid_to__isnull=True).exists():
            continue
        CallSignAssignment.objects.create(
            call_sign=vehicle.call_sign,
            vehicle=vehicle,
            valid_from=vehicle.created_at.date() if vehicle.created_at else heute,
            reason='Bestand bei Einführung der Funkrufnamen-Historie',
        )


def unseed(apps, schema_editor):
    """Die abgeleitete Historie wieder entfernen. Vehicle.call_sign bleibt unberührt."""
    CallSignAssignment = apps.get_model('vehicles', 'CallSignAssignment')
    CallSignAssignment.objects.filter(
        reason='Bestand bei Einführung der Funkrufnamen-Historie'
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('vehicles', '0015_callsignassignment_alter_vehicle_options_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_history, unseed),
    ]
