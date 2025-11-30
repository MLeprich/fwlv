"""
Management Command: Setup Medical Module Permissions
Erstellt die Gruppen für medical_editors und medical_readers mit entsprechenden Permissions
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Erstellt Gruppen und Permissions für das Medical-Modul (Editors & Readers)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Medical Module Permissions Setup ===\n'))

        # Medical Models
        medical_models = [
            'medicalitem',
            'medicalitemmaster',
            'medicaldeviceinstance',
            'medicalstockmovement',
            'medicalbatch',
            'temperaturelog',
        ]

        # ====================================================================
        # 1. Erstelle medical_editors Group
        # ====================================================================
        editors_group, created = Group.objects.get_or_create(name='medical_editors')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Gruppe "medical_editors" erstellt'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Gruppe "medical_editors" existiert bereits'))

        # Füge alle CRUD Permissions hinzu
        editor_permissions = []
        for model_name in medical_models:
            try:
                content_type = ContentType.objects.get(
                    app_label='medical',
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
                f'✓ {len(editor_permissions)} Permissions zu medical_editors hinzugefügt'
            )
        )

        # ====================================================================
        # 2. Erstelle medical_readers Group
        # ====================================================================
        readers_group, created = Group.objects.get_or_create(name='medical_readers')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Gruppe "medical_readers" erstellt'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Gruppe "medical_readers" existiert bereits'))

        # Füge nur View Permissions hinzu
        reader_permissions = []
        for model_name in medical_models:
            try:
                content_type = ContentType.objects.get(
                    app_label='medical',
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
                f'✓ {len(reader_permissions)} Permissions zu medical_readers hinzugefügt'
            )
        )

        # ====================================================================
        # 3. Zusammenfassung
        # ====================================================================
        self.stdout.write('\n' + self.style.SUCCESS('=== Setup abgeschlossen ==='))
        self.stdout.write(f'  • medical_editors: {editors_group.permissions.count()} Permissions')
        self.stdout.write(f'  • medical_readers: {readers_group.permissions.count()} Permissions')
        self.stdout.write(
            '\nModulverantwortliche können nun über /medical/staff-management/ '
            'Benutzer zuweisen.\n'
        )
