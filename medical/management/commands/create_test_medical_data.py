"""
Management Command zum Erstellen von Test-Daten für das Medical Modul
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from medical.models import MedicalItemMaster, MedicalDeviceInstance, MedicalBatch
from locations.models import Location
from inventory_base.models import Category, Supplier

User = get_user_model()


class Command(BaseCommand):
    help = 'Erstellt Test-Daten für Artikel-Stammdaten und Geräte-Instanzen'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Löscht zuerst alle vorhandenen Test-Daten',
        )

    def handle(self, *args, **options):
        # Admin User holen
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                self.stdout.write(self.style.ERROR('Kein Admin-User gefunden. Bitte erstellen Sie zuerst einen Superuser.'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Fehler beim Laden des Users: {e}'))
            return

        # Clear existing data if requested
        if options['clear']:
            self.stdout.write('Lösche vorhandene Test-Daten...')
            MedicalDeviceInstance.objects.all().delete()
            MedicalBatch.objects.filter(master__isnull=False).delete()
            MedicalItemMaster.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Test-Daten gelöscht.'))

        # Kategorie erstellen/holen
        category, _ = Category.objects.get_or_create(
            name='Medizintechnik',
            defaults={
                'description': 'Medizinische Geräte und Technik',
                'created_by': admin_user,
                'updated_by': admin_user,
            }
        )

        # Lieferant erstellen/holen
        supplier, _ = Supplier.objects.get_or_create(
            name='MedTech GmbH',
            defaults={
                'email': 'info@medtech.de',
                'phone': '+49 123 456789',
                'created_by': admin_user,
                'updated_by': admin_user,
            }
        )

        # Lagerort erstellen/holen
        try:
            location = Location.objects.filter(is_active=True).first()
            if not location:
                location = Location.objects.create(
                    name='RTW 1',
                    location_type='vehicle',
                    is_active=True,
                    created_by=admin_user,
                    updated_by=admin_user,
                )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Konnte keinen Lagerort finden: {e}'))
            location = None

        self.stdout.write('Erstelle Artikel-Stammdaten...')

        # 1. Corpuls C3 Defibrillator (Medizintechnik)
        corpuls, created = MedicalItemMaster.objects.get_or_create(
            master_number='MASTER-MED-001',
            defaults={
                'name': 'Corpuls C3 Defibrillator',
                'description': 'Mobiler Defibrillator/Monitor für den Rettungsdienst',
                'item_type': 'device',
                'is_medical_device': True,
                'medical_device_class': 'IIb',
                'manufacturer': 'Corpuls',
                'supplier': supplier,
                'category': category,
                'requires_maintenance': True,
                'maintenance_interval_months': 12,
                'unit': 'Stück',
                'created_by': admin_user,
                'updated_by': admin_user,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Stammdaten: {corpuls.name}'))

        # 2. Oxylog 3000 Plus Beatmungsgerät
        oxylog, created = MedicalItemMaster.objects.get_or_create(
            master_number='MASTER-MED-002',
            defaults={
                'name': 'Oxylog 3000 Plus Beatmungsgerät',
                'description': 'Notfallbeatmungsgerät für Rettungsdienst',
                'item_type': 'device',
                'is_medical_device': True,
                'medical_device_class': 'IIb',
                'manufacturer': 'Dräger',
                'supplier': supplier,
                'category': category,
                'requires_maintenance': True,
                'maintenance_interval_months': 6,
                'unit': 'Stück',
                'created_by': admin_user,
                'updated_by': admin_user,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Stammdaten: {oxylog.name}'))

        # 3. Laryngoskop Set
        laryngoskop, created = MedicalItemMaster.objects.get_or_create(
            master_number='MASTER-MED-003',
            defaults={
                'name': 'Laryngoskop Set',
                'description': 'Komplettes Laryngoskop-Set mit Spatel',
                'item_type': 'device',
                'is_medical_device': True,
                'medical_device_class': 'I',
                'manufacturer': 'Heine',
                'supplier': supplier,
                'category': category,
                'requires_maintenance': False,
                'unit': 'Set',
                'created_by': admin_user,
                'updated_by': admin_user,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Stammdaten: {laryngoskop.name}'))

        # 4. NaCl 0,9% Infusionslösung (Verbrauchsmaterial mit Chargen)
        nacl, created = MedicalItemMaster.objects.get_or_create(
            master_number='MASTER-MED-004',
            defaults={
                'name': 'NaCl 0,9% Infusionslösung 500ml',
                'description': 'Isotonische Kochsalzlösung',
                'item_type': 'infusion',
                'pzn': '1234567',
                'active_ingredient': 'Natriumchlorid',
                'dosage': '0,9%',
                'pharmaceutical_form': 'Infusionslösung',
                'manufacturer': 'B. Braun',
                'supplier': supplier,
                'category': category,
                'unit': 'ml',
                'min_quantity': 5000,
                'max_quantity': 20000,
                'expiry_warning_days': 180,
                'storage_condition': 'room_temp',
                'created_by': admin_user,
                'updated_by': admin_user,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Stammdaten: {nacl.name}'))

        # 5. Adrenalin 1mg/ml Ampullen (BTM-ähnlich, verschreibungspflichtig)
        adrenalin, created = MedicalItemMaster.objects.get_or_create(
            master_number='MASTER-MED-005',
            defaults={
                'name': 'Adrenalin 1mg/ml Ampullen',
                'description': 'Notfallmedikament bei Kreislaufstillstand',
                'item_type': 'medication',
                'pzn': '7654321',
                'active_ingredient': 'Epinephrin',
                'dosage': '1mg/ml',
                'pharmaceutical_form': 'Ampullen',
                'administration_route': 'iv',
                'manufacturer': 'Sanofi',
                'supplier': supplier,
                'category': category,
                'unit': 'Ampulle',
                'min_quantity': 50,
                'max_quantity': 200,
                'expiry_warning_days': 90,
                'storage_condition': 'room_temp',
                'is_prescription_required': True,
                'requires_cold_chain': False,
                'created_by': admin_user,
                'updated_by': admin_user,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Stammdaten: {adrenalin.name}'))

        # Geräte-Instanzen erstellen (nur wenn Location vorhanden)
        if location:
            self.stdout.write('\nErstelle Geräte-Instanzen...')

            # Corpuls C3 Instanzen
            for i in range(1, 4):
                device, created = MedicalDeviceInstance.objects.get_or_create(
                    inventory_number=f'DEV-CORPULS-{i:03d}',
                    defaults={
                        'master': corpuls,
                        'serial_number': f'CORP-{2020+i}-{1000+i}',
                        'location': location,
                        'purchase_date': timezone.now().date() - timedelta(days=365*i),
                        'commissioning_date': timezone.now().date() - timedelta(days=365*i),
                        'last_maintenance_date': timezone.now().date() - timedelta(days=30*i),
                        'next_maintenance_date': timezone.now().date() + timedelta(days=365-30*i),
                        'last_inspection_date': timezone.now().date() - timedelta(days=15*i),
                        'next_inspection_date': timezone.now().date() + timedelta(days=90-15*i),
                        'purchase_price': 25000.00,
                        'condition': 'good' if i <= 2 else 'fair',
                        'is_operational': True,
                        'created_by': admin_user,
                        'updated_by': admin_user,
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Gerät: {device.inventory_number}'))

            # Oxylog 3000 Plus Instanzen
            for i in range(1, 3):
                device, created = MedicalDeviceInstance.objects.get_or_create(
                    inventory_number=f'DEV-OXYLOG-{i:03d}',
                    defaults={
                        'master': oxylog,
                        'serial_number': f'OXYLOG-{2021+i}-{2000+i}',
                        'location': location,
                        'purchase_date': timezone.now().date() - timedelta(days=200*i),
                        'commissioning_date': timezone.now().date() - timedelta(days=200*i),
                        'last_maintenance_date': timezone.now().date() - timedelta(days=45*i),
                        'next_maintenance_date': timezone.now().date() + timedelta(days=180-45*i),
                        'purchase_price': 18000.00,
                        'condition': 'good',
                        'is_operational': True,
                        'created_by': admin_user,
                        'updated_by': admin_user,
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Gerät: {device.inventory_number}'))

            # Laryngoskop Sets
            for i in range(1, 6):
                device, created = MedicalDeviceInstance.objects.get_or_create(
                    inventory_number=f'DEV-LARYNGO-{i:03d}',
                    defaults={
                        'master': laryngoskop,
                        'serial_number': f'HEINE-{2022}-{3000+i}',
                        'location': location,
                        'purchase_date': timezone.now().date() - timedelta(days=100*i),
                        'commissioning_date': timezone.now().date() - timedelta(days=100*i),
                        'purchase_price': 450.00,
                        'condition': 'good',
                        'is_operational': True,
                        'created_by': admin_user,
                        'updated_by': admin_user,
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Gerät: {device.inventory_number}'))

        # Chargen erstellen für Verbrauchsmaterialien
        if location:
            self.stdout.write('\nErstelle Chargen...')

            # NaCl Chargen
            for i in range(1, 4):
                batch, created = MedicalBatch.objects.get_or_create(
                    batch_number=f'NACL-2025-{1000+i}',
                    master=nacl,
                    defaults={
                        'received_date': timezone.now().date() - timedelta(days=30*i),
                        'expiry_date': timezone.now().date() + timedelta(days=730-30*i),
                        'quantity_received': 10000,
                        'quantity_remaining': 10000 - (1000*i),
                        'location': location,
                        'supplier_batch_number': f'BB-{2025}-{2000+i}',
                        'notes': f'Test-Charge {i}',
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Charge: {batch.batch_number}'))

            # Adrenalin Chargen
            for i in range(1, 3):
                batch, created = MedicalBatch.objects.get_or_create(
                    batch_number=f'ADRE-2025-{3000+i}',
                    master=adrenalin,
                    defaults={
                        'received_date': timezone.now().date() - timedelta(days=60*i),
                        'expiry_date': timezone.now().date() + timedelta(days=365-60*i),
                        'quantity_received': 100,
                        'quantity_remaining': 100 - (20*i),
                        'location': location,
                        'supplier_batch_number': f'SAN-{2025}-{4000+i}',
                        'notes': f'Test-Charge {i}',
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Charge: {batch.batch_number}'))

        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('✓ Test-Daten erfolgreich erstellt!'))
        self.stdout.write('='*50)
        self.stdout.write('\nErstellte Daten:')
        self.stdout.write(f'  • {MedicalItemMaster.objects.count()} Artikel-Stammdaten')
        self.stdout.write(f'  • {MedicalDeviceInstance.objects.count()} Geräte-Instanzen')
        self.stdout.write(f'  • {MedicalBatch.objects.filter(master__isnull=False).count()} Chargen')
        self.stdout.write('\nZugriff:')
        self.stdout.write('  • Stammdaten: /medical/masters/')
        self.stdout.write('  • Geräte: /medical/devices/')
        self.stdout.write('  • Chargen: /medical/batches/')
