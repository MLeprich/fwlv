"""
Management Command zum Migrieren der Equipment Types von Enum zu DB
"""

from django.core.management.base import BaseCommand
from height_rescue.models import EquipmentType, HeightRescueItemType


class Command(BaseCommand):
    help = 'Migriert Equipment Types von Enum zu Datenbank'

    def handle(self, *args, **options):
        self.stdout.write('Migriere Equipment Types...')

        # Erstelle EquipmentType-Einträge aus dem Enum
        types_created = 0
        for order, (code, name) in enumerate(HeightRescueItemType.choices):
            equipment_type, created = EquipmentType.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'is_active': True,
                    'order': order,
                }
            )
            if created:
                types_created += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ {equipment_type.name} ({equipment_type.code})'))
            else:
                self.stdout.write(f'  - {equipment_type.name} ({equipment_type.code}) existiert bereits')

        self.stdout.write(self.style.SUCCESS(f'\n{types_created} neue Equipment Types erstellt'))
        self.stdout.write(self.style.SUCCESS('Migration abgeschlossen!'))
