"""
Management Command: Setup IT Hardware Module Permissions
Erstellt die Gruppen für it_hardware_editors und it_hardware_readers mit entsprechenden Permissions
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Erstellt Gruppen und Permissions für das IT-Hardware-Modul (Editors & Readers)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== IT Hardware Module Permissions Setup ===\n'))

        # IT Hardware Models
        it_hardware_models = [
            'ithardwareitemmaster',
            'ithardwaredeviceinstance',
            'ithardwarestockmovement',
        ]

        # ====================================================================
        # 1. Erstelle it_hardware_editors Group
        # ====================================================================
        editors_group, created = Group.objects.get_or_create(name='it_hardware_editors')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Gruppe "it_hardware_editors" erstellt'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Gruppe "it_hardware_editors" existiert bereits'))

        # Füge alle CRUD Permissions hinzu
        editor_permissions = []
        for model_name in it_hardware_models:
            try:
                content_type = ContentType.objects.get(
                    app_label='it_hardware',
                    model=model_name
                )

                for action in ['add', 'change', 'delete', 'view']:
                    perm = Permission.objects.get(
                        content_type=content_type,
                        codename=f'{action}_{model_name}'
                    )
                    editor_permissions.append(perm)

            except (ContentType.DoesNotExist, Permission.DoesNotExist) as e:
                self.stdout.write(self.style.ERROR(f'✗ Fehler bei {model_name}: {e}'))

        # Setze Permissions
        editors_group.permissions.set(editor_permissions)
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ {len(editor_permissions)} Permissions zu it_hardware_editors hinzugefügt'
            )
        )

        # ====================================================================
        # 2. Erstelle it_hardware_readers Group
        # ====================================================================
        readers_group, created = Group.objects.get_or_create(name='it_hardware_readers')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Gruppe "it_hardware_readers" erstellt'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Gruppe "it_hardware_readers" existiert bereits'))

        # Füge nur View Permissions hinzu
        reader_permissions = []
        for model_name in it_hardware_models:
            try:
                content_type = ContentType.objects.get(
                    app_label='it_hardware',
                    model=model_name
                )

                perm = Permission.objects.get(
                    content_type=content_type,
                    codename=f'view_{model_name}'
                )
                reader_permissions.append(perm)

            except (ContentType.DoesNotExist, Permission.DoesNotExist) as e:
                self.stdout.write(self.style.ERROR(f'✗ Fehler bei {model_name}: {e}'))

        # Setze Permissions
        readers_group.permissions.set(reader_permissions)
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ {len(reader_permissions)} Permissions zu it_hardware_readers hinzugefügt'
            )
        )

        # ====================================================================
        # 3. Zusammenfassung
        # ====================================================================
        self.stdout.write('\n' + self.style.SUCCESS('=== Setup abgeschlossen ==='))
        self.stdout.write(f'  • it_hardware_editors: {editors_group.permissions.count()} Permissions')
        self.stdout.write(f'  • it_hardware_readers: {readers_group.permissions.count()} Permissions')
        self.stdout.write(
            '\nModulverantwortliche können nun über /it_hardware/staff-management/ '
            'Benutzer zuweisen.\n'
        )
