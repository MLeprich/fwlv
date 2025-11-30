"""
Management Command: Setup Workshop Module Permissions
Erstellt die Gruppen für workshop_editors und workshop_readers mit entsprechenden Permissions
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Erstellt Gruppen und Permissions für das Workshop-Modul (Editors & Readers)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Workshop Module Permissions Setup ===\n'))

        # Workshop Models
        workshop_models = [
            'workshopitemmaster',
            'workshoptoolinstance',
            'workshopstockmovement',
            'vehicleservicerecord',
        ]

        # ====================================================================
        # 1. Erstelle workshop_editors Group
        # ====================================================================
        editors_group, created = Group.objects.get_or_create(name='workshop_editors')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Gruppe "workshop_editors" erstellt'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Gruppe "workshop_editors" existiert bereits'))

        # Füge alle CRUD Permissions hinzu
        editor_permissions = []
        for model_name in workshop_models:
            try:
                content_type = ContentType.objects.get(
                    app_label='workshop',
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
                f'✓ {len(editor_permissions)} Permissions zu workshop_editors hinzugefügt'
            )
        )

        # ====================================================================
        # 2. Erstelle workshop_readers Group
        # ====================================================================
        readers_group, created = Group.objects.get_or_create(name='workshop_readers')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Gruppe "workshop_readers" erstellt'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Gruppe "workshop_readers" existiert bereits'))

        # Füge nur View Permissions hinzu
        reader_permissions = []
        for model_name in workshop_models:
            try:
                content_type = ContentType.objects.get(
                    app_label='workshop',
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
                f'✓ {len(reader_permissions)} Permissions zu workshop_readers hinzugefügt'
            )
        )

        # ====================================================================
        # 3. Zusammenfassung
        # ====================================================================
        self.stdout.write('\n' + self.style.SUCCESS('=== Setup abgeschlossen ==='))
        self.stdout.write(f'  • workshop_editors: {editors_group.permissions.count()} Permissions')
        self.stdout.write(f'  • workshop_readers: {readers_group.permissions.count()} Permissions')
        self.stdout.write(
            '\nModulverantwortliche können nun über /workshop/staff-management/ '
            'Benutzer zuweisen.\n'
        )
