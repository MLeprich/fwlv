"""
Management Command: Setup Objektverwaltung Module Permissions

Erstellt die Gruppen 'objektverwaltung_editors' (volle CRUD-Rechte) und
'objektverwaltung_readers' (nur Lesen) mit den passenden Permissions.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Erstellt Gruppen und Permissions für das Objektverwaltung-Modul'

    MODELS = [
        'buildingobject',
        'floor',
        'escaperoute',
        'firealarmpanel',
        'firesuppressionsystem',
        'compensationmeasure',
        'buildingcontact',
        'buildingplan',
        'firekeydepot',
        'fsdinspectionreport',
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Objektverwaltung Permissions Setup ===\n'))

        editors, created = Group.objects.get_or_create(name='objektverwaltung_editors')
        self.stdout.write(self.style.SUCCESS(
            '✓ Gruppe "objektverwaltung_editors" %s' % ('erstellt' if created else 'vorhanden')
        ))

        readers, created = Group.objects.get_or_create(name='objektverwaltung_readers')
        self.stdout.write(self.style.SUCCESS(
            '✓ Gruppe "objektverwaltung_readers" %s' % ('erstellt' if created else 'vorhanden')
        ))

        editor_perms = []
        reader_perms = []
        for model_name in self.MODELS:
            try:
                ct = ContentType.objects.get(app_label='objektverwaltung', model=model_name)
            except ContentType.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'✗ ContentType für {model_name} fehlt'))
                continue

            for action in ['add', 'change', 'delete', 'view']:
                try:
                    perm = Permission.objects.get(content_type=ct, codename=f'{action}_{model_name}')
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'✗ Permission {action}_{model_name} fehlt'))
                    continue
                editor_perms.append(perm)
                if action == 'view':
                    reader_perms.append(perm)

        editors.permissions.set(editor_perms)
        readers.permissions.set(reader_perms)

        self.stdout.write('\n' + self.style.SUCCESS('=== Setup abgeschlossen ==='))
        self.stdout.write(f'  • objektverwaltung_editors: {editors.permissions.count()} Permissions')
        self.stdout.write(f'  • objektverwaltung_readers: {readers.permissions.count()} Permissions\n')
