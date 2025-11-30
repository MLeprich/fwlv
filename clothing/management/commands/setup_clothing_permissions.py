"""
Management Command: Setup Clothing Module Permissions
Erstellt die Gruppen für clothing_editors und clothing_readers mit entsprechenden Permissions
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Erstellt Gruppen und Permissions für das Clothing-Modul (Editors & Readers)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Clothing Module Permissions Setup ===\n'))

        # Clothing Models
        clothing_models = [
            'clothingitem',
            'clothingstockmovement',
            'clothingcategory',
            'clothingsizeassignment',
        ]

        # ====================================================================
        # 1. Erstelle clothing_editors Group
        # ====================================================================
        editors_group, created = Group.objects.get_or_create(name='clothing_editors')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Gruppe "clothing_editors" erstellt'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Gruppe "clothing_editors" existiert bereits'))

        # Füge alle CRUD Permissions hinzu
        editor_permissions = []
        for model_name in clothing_models:
            try:
                content_type = ContentType.objects.get(
                    app_label='clothing',
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
                f'✓ {len(editor_permissions)} Permissions zu clothing_editors hinzugefügt'
            )
        )

        # ====================================================================
        # 2. Erstelle clothing_readers Group
        # ====================================================================
        readers_group, created = Group.objects.get_or_create(name='clothing_readers')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Gruppe "clothing_readers" erstellt'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Gruppe "clothing_readers" existiert bereits'))

        # Füge nur View Permissions hinzu
        reader_permissions = []
        for model_name in clothing_models:
            try:
                content_type = ContentType.objects.get(
                    app_label='clothing',
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
                f'✓ {len(reader_permissions)} Permissions zu clothing_readers hinzugefügt'
            )
        )

        # ====================================================================
        # 3. Zusammenfassung
        # ====================================================================
        self.stdout.write('\n' + self.style.SUCCESS('=== Setup abgeschlossen ==='))
        self.stdout.write(f'  • clothing_editors: {editors_group.permissions.count()} Permissions')
        self.stdout.write(f'  • clothing_readers: {readers_group.permissions.count()} Permissions')
        self.stdout.write(
            '\nModulverantwortliche können nun über /clothing/staff-management/ '
            'Benutzer zuweisen.\n'
        )
