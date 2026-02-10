"""
Migration 2/3: Data migration - create VehicleType entries and link existing vehicles
"""

from django.db import migrations


# Seed data from old TextChoices enum
VEHICLE_TYPE_DATA = [
    {'code': 'fire_truck', 'name': 'Löschfahrzeug', 'icon': '🚒', 'order': 1},
    {'code': 'command', 'name': 'Kommandowagen', 'icon': '🚗', 'order': 2},
    {'code': 'ambulance', 'name': 'Rettungswagen', 'icon': '🚑', 'order': 3},
    {'code': 'ladder', 'name': 'Drehleiter', 'icon': '🪜', 'order': 4},
    {'code': 'special', 'name': 'Sonderfahrzeug', 'icon': '🚛', 'order': 5},
    {'code': 'trailer', 'name': 'Anhänger', 'icon': '🚛', 'order': 6},
    {'code': 'boat', 'name': 'Boot', 'icon': '🚤', 'order': 7},
    {'code': 'utility', 'name': 'Mannschaftstransporter', 'icon': '🚐', 'order': 8},
    {'code': 'other', 'name': 'Sonstiges', 'icon': '🚙', 'order': 9},
]


def forwards(apps, schema_editor):
    VehicleType = apps.get_model('vehicles', 'VehicleType')
    Vehicle = apps.get_model('vehicles', 'Vehicle')
    VehicleModel = apps.get_model('vehicles', 'VehicleModel')

    # 1. Create VehicleType entries from seed data
    type_map = {}
    for data in VEHICLE_TYPE_DATA:
        vt, _ = VehicleType.objects.get_or_create(
            code=data['code'],
            defaults={
                'name': data['name'],
                'icon': data['icon'],
                'order': data['order'],
            }
        )
        type_map[data['code']] = vt

    # 2. Link existing vehicles to new VehicleType FK
    for vehicle in Vehicle.objects.all():
        if vehicle.vehicle_type and vehicle.vehicle_type in type_map:
            vehicle.vehicle_type_new = type_map[vehicle.vehicle_type]
            vehicle.save(update_fields=['vehicle_type_new'])

    # 3. Link existing vehicle models to new VehicleType FK
    for vm in VehicleModel.objects.all():
        if vm.vehicle_type and vm.vehicle_type in type_map:
            vm.vehicle_type_new = type_map[vm.vehicle_type]
            vm.save(update_fields=['vehicle_type_new'])


def backwards(apps, schema_editor):
    VehicleType = apps.get_model('vehicles', 'VehicleType')
    Vehicle = apps.get_model('vehicles', 'Vehicle')
    VehicleModel = apps.get_model('vehicles', 'VehicleModel')

    # Reverse: copy FK back to CharField
    for vehicle in Vehicle.objects.select_related('vehicle_type_new').all():
        if vehicle.vehicle_type_new:
            vehicle.vehicle_type = vehicle.vehicle_type_new.code
            vehicle.save(update_fields=['vehicle_type'])

    for vm in VehicleModel.objects.select_related('vehicle_type_new').all():
        if vm.vehicle_type_new:
            vm.vehicle_type = vm.vehicle_type_new.code
            vm.save(update_fields=['vehicle_type'])


class Migration(migrations.Migration):

    dependencies = [
        ('vehicles', '0008_vehicletype_model'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
