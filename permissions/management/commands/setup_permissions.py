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
from django.db.models import Q

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
                self._setup_sachbearbeiter_modules()
                self._setup_lagerverwalter()
                self._setup_wachleiter()
                self._setup_sachbearbeiter()
                self._setup_standard_user()
                self._setup_approval_groups()
                self._setup_lst_infomonitor()
                self._cleanup_legacy_groups()

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
            Modules.VEHICLES: 'KFZ',
            Modules.PROCUREMENT: 'Procurement',
            Modules.DEFECT_MANAGEMENT: 'Defect Management',
            Modules.CIVIL_PROTECTION: 'Civil Protection',
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
            # Medical: BTM-Permissions ausschließen (nur BTM-Beauftragter)
            if module_name == Modules.MEDICAL:
                module_perms = module_perms.exclude(codename__icontains='btm')
            for perm in module_perms:
                group.permissions.add(perm)
                perms_added += 1

            # Plus: Bestellfreigabe bis 1.000€ (nicht für Procurement selbst, da bereits enthalten)
            if module_name != Modules.PROCUREMENT:
                try:
                    procurement_perms = Permission.objects.filter(
                        content_type__app_label=Modules.PROCUREMENT,
                        codename__in=['create_order_request', 'view_own_orders', 'approve_order_low']
                    )
                    for perm in procurement_perms:
                        group.permissions.add(perm)
                        perms_added += 1
                except Permission.DoesNotExist:
                    pass

            # Inventur-Permissions für Lager-Module
            if module_name in Modules.get_inventory_modules():
                inventory_perms = Permission.objects.filter(
                    content_type__app_label=Modules.INVENTORY_CHECK
                )
                for perm in inventory_perms:
                    group.permissions.add(perm)
                    perms_added += 1

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

    def _setup_sachbearbeiter_modules(self):
        """Sachbearbeiter pro Modul (view + add, kein change/delete)"""
        self.stdout.write('\n4b. Sachbearbeiter pro Modul...')

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
            Modules.VEHICLES: 'KFZ',
            Modules.PROCUREMENT: 'Procurement',
            Modules.DEFECT_MANAGEMENT: 'Defect Management',
            Modules.CIVIL_PROTECTION: 'Civil Protection',
        }

        for module_name, display_name in modules.items():
            group_name = f'Sachbearbeiter {display_name}'
            group, created = Group.objects.get_or_create(name=group_name)
            group.permissions.clear()

            perms_added = 0

            # Nur view_* und add_* Permissions für dieses Modul
            module_perms = Permission.objects.filter(
                content_type__app_label=module_name
            ).filter(
                Q(codename__startswith='view_') | Q(codename__startswith='add_')
            )
            for perm in module_perms:
                group.permissions.add(perm)
                perms_added += 1

            status = 'erstellt' if created else 'aktualisiert'
            self.stdout.write(
                f'  ✓ Sachbearbeiter {display_name}: {status} ({perms_added} Permissions)'
            )

    def _setup_lagerverwalter(self):
        """Lagerverwalter Gruppe - Nur Standorte & Lagerorte"""
        self.stdout.write('\n5. Lagerverwalter...')

        group, created = Group.objects.get_or_create(name=Roles.LAGERVERWALTER)
        group.permissions.clear()

        perms_added = 0

        # Locations: Vollzugriff (CRUD)
        location_perms = Permission.objects.filter(
            content_type__app_label=Modules.LOCATIONS
        )
        for perm in location_perms:
            group.permissions.add(perm)
            perms_added += 1

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

    def _setup_approval_groups(self):
        """Freigabe-Gruppen für Bestellwesen (Stufe 1/2/3)"""
        self.stdout.write('\n9. Freigabe-Gruppen...')

        approval_groups = {
            Roles.FREIGABE_STUFE_1: {
                'description': 'Freigabe bis 1.000 EUR',
                'codenames': ['approve_order_low', 'view_own_orders', 'create_order_request'],
            },
            Roles.FREIGABE_STUFE_2: {
                'description': 'Freigabe bis 5.000 EUR',
                'codenames': ['approve_order_low', 'approve_order_medium', 'view_own_orders', 'create_order_request'],
            },
            Roles.FREIGABE_STUFE_3: {
                'description': 'Unbegrenzte Freigabe',
                'codenames': ['approve_order_low', 'approve_order_medium', 'approve_order_high', 'view_own_orders', 'create_order_request', 'cancel_order'],
            },
        }

        for group_name, config in approval_groups.items():
            group, created = Group.objects.get_or_create(name=group_name)
            group.permissions.clear()

            perms_added = 0
            for codename in config['codenames']:
                try:
                    perm = Permission.objects.get(
                        content_type__app_label=Modules.PROCUREMENT,
                        codename=codename
                    )
                    group.permissions.add(perm)
                    perms_added += 1
                except Permission.DoesNotExist:
                    pass

            # Auch View-Rechte für Procurement-Modelle
            view_perms = Permission.objects.filter(
                content_type__app_label=Modules.PROCUREMENT,
                codename__startswith='view_'
            )
            for perm in view_perms:
                group.permissions.add(perm)
                perms_added += 1

            status = 'erstellt' if created else 'aktualisiert'
            self.stdout.write(
                self.style.SUCCESS(
                    f'  ✓ {group_name}: {status} ({perms_added} Permissions) - {config["description"]}'
                )
            )

    def _setup_lst_infomonitor(self):
        """LST Infomonitor Gruppe"""
        self.stdout.write('\n10. LST Infomonitor...')

        group, created = Group.objects.get_or_create(name=Roles.LST_INFOMONITOR)
        group.permissions.clear()

        perms_added = 0
        for codename in ['edit_infomonitor', 'view_infomonitor']:
            try:
                perm = Permission.objects.get(
                    content_type__app_label='tickets',
                    codename=codename
                )
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

    def _cleanup_legacy_groups(self):
        """Entfernt veraltete Gruppen die nicht mehr verwendet werden"""
        self.stdout.write('\n9. Bereinigung veralteter Gruppen...')

        legacy_groups = [
            'Modulverantwortlicher',  # Alte generische Gruppe ohne Modulname
        ]

        for group_name in legacy_groups:
            try:
                group = Group.objects.get(name=group_name)
                user_count = group.user_set.count()
                if user_count > 0:
                    usernames = list(group.user_set.values_list('username', flat=True))
                    group.user_set.clear()
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ✓ {group_name}: {user_count} User entfernt ({", ".join(usernames)})'
                        )
                    )
                group.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ {group_name}: gelöscht')
                )
            except Group.DoesNotExist:
                pass

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
