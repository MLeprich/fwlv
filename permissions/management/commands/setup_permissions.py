"""
Management Command zum Erstellen aller Permission-Gruppen (Rollen)
und Zuweisung der entsprechenden Permissions

Usage:
    python manage.py setup_permissions
    python manage.py setup_permissions --reset  # Löscht zuerst alle Gruppen
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from permissions.constants import Roles, Modules, Actions, CustomPermissions


class Command(BaseCommand):
    help = 'Erstellt alle Rollen-Gruppen und weist Permissions zu'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Löscht alle Gruppen vor der Erstellung (VORSICHT!)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simuliert die Ausführung ohne Änderungen',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=== Permission Setup ==='))

        if options['reset']:
            if not options['dry_run']:
                self.stdout.write(self.style.WARNING('WARNUNG: Alle Gruppen werden gelöscht!'))
                confirm = input('Fortfahren? (ja/nein): ')
                if confirm.lower() not in ['ja', 'yes', 'y']:
                    self.stdout.write(self.style.ERROR('Abgebrochen.'))
                    return

                self._reset_groups()
            else:
                self.stdout.write(self.style.NOTICE('[DRY RUN] Würde alle Gruppen löschen'))

        try:
            with transaction.atomic():
                self._setup_administrator()
                self._setup_btm_beauftragter()
                self._setup_werkstattmeister()
                self._setup_module_leads()
                self._setup_lagerverwalter()
                self._setup_wachleiter()
                self._setup_sachbearbeiter()
                self._setup_standard_user()

                if options['dry_run']:
                    raise CommandError('DRY RUN - Keine Änderungen vorgenommen')

            self.stdout.write(self.style.SUCCESS('\n✓ Gruppen erfolgreich erstellt!'))
            self._print_summary()

        except CommandError:
            self.stdout.write(self.style.NOTICE('\nDRY RUN abgeschlossen'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Fehler: {str(e)}'))
            raise

    def _reset_groups(self):
        """Löscht alle Gruppen"""
        count = Group.objects.all().count()
        Group.objects.all().delete()
        self.stdout.write(self.style.WARNING(f'✓ {count} Gruppen gelöscht'))

    def _setup_administrator(self):
        """Administrator-Gruppe mit Vollzugriff"""
        self.stdout.write('\n1. Administrator...')

        group, created = Group.objects.get_or_create(name=Roles.ADMINISTRATOR)

        # Alle Permissions
        all_perms = Permission.objects.all()
        group.permissions.set(all_perms)

        status = 'erstellt' if created else 'aktualisiert'
        self.stdout.write(
            self.style.SUCCESS(
                f'  ✓ {status} ({all_perms.count()} Permissions)'
            )
        )

    def _setup_btm_beauftragter(self):
        """BTM-Beauftragter Gruppe"""
        self.stdout.write('\n2. BTM-Beauftragter...')

        group, created = Group.objects.get_or_create(name=Roles.BTM_BEAUFTRAGTER)
        group.permissions.clear()

        # Medical App Permissions
        perms_added = 0

        # Standard CRUD für Medical
        medical_perms = Permission.objects.filter(
            content_type__app_label=Modules.MEDICAL
        )
        for perm in medical_perms:
            group.permissions.add(perm)
            perms_added += 1

        # Reporting für BTM
        try:
            reporting_perm = Permission.objects.get(
                content_type__app_label=Modules.REPORTING,
                codename='view_btm_reports'
            )
            group.permissions.add(reporting_perm)
            perms_added += 1
        except Permission.DoesNotExist:
            pass

        status = 'erstellt' if created else 'aktualisiert'
        self.stdout.write(
            self.style.SUCCESS(
                f'  ✓ {status} ({perms_added} Permissions)'
            )
        )

    def _setup_werkstattmeister(self):
        """Werkstattmeister Gruppe"""
        self.stdout.write('\n3. Werkstattmeister...')

        group, created = Group.objects.get_or_create(name=Roles.WERKSTATTMEISTER)
        group.permissions.clear()

        perms_added = 0

        # Workshop: Vollzugriff
        workshop_perms = Permission.objects.filter(
            content_type__app_label=Modules.WORKSHOP
        )
        for perm in workshop_perms:
            group.permissions.add(perm)
            perms_added += 1

        # Vehicles: View + Change
        vehicle_perms = Permission.objects.filter(
            content_type__app_label=Modules.VEHICLES,
            codename__in=['view_vehicle', 'change_vehicle', 'view_vehicleinspection',
                          'add_vehicleinspection', 'change_vehicleinspection']
        )
        for perm in vehicle_perms:
            group.permissions.add(perm)
            perms_added += 1

        # Procurement: Bestellungen bis 1.000€
        try:
            procurement_perms = Permission.objects.filter(
                content_type__app_label=Modules.PROCUREMENT,
                codename__in=['create_order_request', 'view_order', 'approve_order_low']
            )
            for perm in procurement_perms:
                group.permissions.add(perm)
                perms_added += 1
        except Permission.DoesNotExist:
            pass

        status = 'erstellt' if created else 'aktualisiert'
        self.stdout.write(
            self.style.SUCCESS(
                f'  ✓ {status} ({perms_added} Permissions)'
            )
        )

    def _setup_module_leads(self):
        """Modulverantwortliche für alle Lager-Module"""
        self.stdout.write('\n4. Modulverantwortliche...')

        modules = {
            Modules.MEDICAL: 'Medical',
            Modules.CLOTHING: 'Clothing',
            Modules.MAGAZINE: 'Magazine',
            Modules.WORKSHOP: 'Workshop',
            Modules.DISINFECTION: 'Disinfection',
            Modules.HEIGHT_RESCUE: 'Height Rescue',
            Modules.DIVING: 'Diving',
            Modules.EQUIPMENT: 'Equipment',
            Modules.IT_HARDWARE: 'IT Hardware',
            Modules.WIKI: 'Wiki',
            Modules.INFO_MONITORS: 'Info Monitors',
        }

        for module_name, display_name in modules.items():
            group_name = f'Modulverantwortlicher {display_name}'
            group, created = Group.objects.get_or_create(name=group_name)
            group.permissions.clear()

            perms_added = 0

            # Alle Permissions für dieses Modul
            module_perms = Permission.objects.filter(
                content_type__app_label=module_name
            )
            for perm in module_perms:
                group.permissions.add(perm)
                perms_added += 1

            # Plus: Bestellfreigabe bis 1.000€
            try:
                procurement_perms = Permission.objects.filter(
                    content_type__app_label=Modules.PROCUREMENT,
                    codename__in=['create_order_request', 'view_order', 'approve_order_low']
                )
                for perm in procurement_perms:
                    group.permissions.add(perm)
                    perms_added += 1
            except Permission.DoesNotExist:
                pass

            # Reporting für Modul
            try:
                reporting_perm = Permission.objects.get(
                    content_type__app_label=Modules.REPORTING,
                    codename='view_module_reports'
                )
                group.permissions.add(reporting_perm)
                perms_added += 1
            except Permission.DoesNotExist:
                pass

            status = 'erstellt' if created else 'aktualisiert'
            self.stdout.write(
                f'  ✓ {display_name}: {status} ({perms_added} Permissions)'
            )

    def _setup_lagerverwalter(self):
        """Lagerverwalter Gruppe"""
        self.stdout.write('\n5. Lagerverwalter...')

        group, created = Group.objects.get_or_create(name=Roles.LAGERVERWALTER)
        group.permissions.clear()

        perms_added = 0

        # View + Add für alle Lager-Module
        inventory_modules = Modules.get_inventory_modules()

        for module in inventory_modules:
            module_perms = Permission.objects.filter(
                content_type__app_label=module,
                codename__startswith=('view_', 'add_')
            )
            for perm in module_perms:
                group.permissions.add(perm)
                perms_added += 1

        # Inventur
        try:
            inventory_perms = Permission.objects.filter(
                content_type__app_label=Modules.INVENTORY_CHECK
            )
            for perm in inventory_perms:
                group.permissions.add(perm)
                perms_added += 1
        except Permission.DoesNotExist:
            pass

        # Locations: View
        try:
            location_perms = Permission.objects.filter(
                content_type__app_label=Modules.LOCATIONS,
                codename__startswith='view_'
            )
            for perm in location_perms:
                group.permissions.add(perm)
                perms_added += 1
        except Permission.DoesNotExist:
            pass

        status = 'erstellt' if created else 'aktualisiert'
        self.stdout.write(
            self.style.SUCCESS(
                f'  ✓ {status} ({perms_added} Permissions)'
            )
        )

    def _setup_wachleiter(self):
        """Wachleiter Gruppe"""
        self.stdout.write('\n6. Wachleiter...')

        group, created = Group.objects.get_or_create(name=Roles.WACHLEITER)
        group.permissions.clear()

        perms_added = 0

        # Fahrzeugübernahme: Vollzugriff
        try:
            handover_perms = Permission.objects.filter(
                content_type__app_label=Modules.VEHICLE_HANDOVER
            )
            for perm in handover_perms:
                group.permissions.add(perm)
                perms_added += 1
        except Permission.DoesNotExist:
            pass

        # View-Rechte für wichtige Module
        view_modules = [
            Modules.VEHICLES,
            Modules.PERSONNEL,
            Modules.MEDICAL,
            Modules.MAGAZINE,
            Modules.EQUIPMENT,
        ]

        for module in view_modules:
            view_perms = Permission.objects.filter(
                content_type__app_label=module,
                codename__startswith='view_'
            )
            for perm in view_perms:
                group.permissions.add(perm)
                perms_added += 1

        # Bestellanfragen erstellen
        try:
            procurement_perm = Permission.objects.get(
                content_type__app_label=Modules.PROCUREMENT,
                codename='create_order_request'
            )
            group.permissions.add(procurement_perm)
            perms_added += 1
        except Permission.DoesNotExist:
            pass

        status = 'erstellt' if created else 'aktualisiert'
        self.stdout.write(
            self.style.SUCCESS(
                f'  ✓ {status} ({perms_added} Permissions)'
            )
        )

    def _setup_sachbearbeiter(self):
        """Sachbearbeiter Gruppe"""
        self.stdout.write('\n7. Sachbearbeiter...')

        group, created = Group.objects.get_or_create(name=Roles.SACHBEARBEITER)
        group.permissions.clear()

        perms_added = 0

        # View-Rechte für fast alle Module
        view_perms = Permission.objects.filter(
            codename__startswith='view_'
        ).exclude(
            # Kein BTM-Zugriff
            content_type__app_label=Modules.MEDICAL,
            codename__contains='btm'
        )

        for perm in view_perms:
            group.permissions.add(perm)
            perms_added += 1

        # Dokumente: Add + Change eigene
        try:
            doc_perms = Permission.objects.filter(
                content_type__app_label=Modules.DOCUMENTS,
                codename__in=['add_document', 'view_document', 'change_own_document']
            )
            for perm in doc_perms:
                group.permissions.add(perm)
                perms_added += 1
        except Permission.DoesNotExist:
            pass

        # Procurement: Bestellanfragen
        try:
            procurement_perms = Permission.objects.filter(
                content_type__app_label=Modules.PROCUREMENT,
                codename__in=['create_order_request', 'view_order']
            )
            for perm in procurement_perms:
                group.permissions.add(perm)
                perms_added += 1
        except Permission.DoesNotExist:
            pass

        status = 'erstellt' if created else 'aktualisiert'
        self.stdout.write(
            self.style.SUCCESS(
                f'  ✓ {status} ({perms_added} Permissions)'
            )
        )

    def _setup_standard_user(self):
        """Standard-Nutzer Gruppe"""
        self.stdout.write('\n8. Standard-Nutzer...')

        group, created = Group.objects.get_or_create(name=Roles.STANDARD_USER)
        group.permissions.clear()

        perms_added = 0

        # Sehr eingeschränkte Permissions
        basic_modules = [Modules.PERSONNEL, Modules.VEHICLES]

        for module in basic_modules:
            view_perms = Permission.objects.filter(
                content_type__app_label=module,
                codename__startswith='view_'
            )
            for perm in view_perms:
                group.permissions.add(perm)
                perms_added += 1

        status = 'erstellt' if created else 'aktualisiert'
        self.stdout.write(
            self.style.SUCCESS(
                f'  ✓ {status} ({perms_added} Permissions)'
            )
        )

    def _print_summary(self):
        """Gibt Zusammenfassung aus"""
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Zusammenfassung ==='))

        groups = Group.objects.all().order_by('name')

        for group in groups:
            perm_count = group.permissions.count()
            user_count = group.user_set.count()

            self.stdout.write(
                f'{group.name:35} | {perm_count:3} Permissions | {user_count:3} User'
            )

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f'\nGesamt: {groups.count()} Gruppen'
            )
        )
