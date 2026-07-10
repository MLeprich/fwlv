"""Legt die Rolle „Unfallbeauftragter" mit den Unfallbericht-Rechten an."""

from django.db import migrations

GROUP_NAME = 'Unfallbeauftragter'

PERMISSIONS = [
    ('view_accidentreport', 'Can view Unfallbericht'),
    ('add_accidentreport', 'Can add Unfallbericht'),
    ('change_accidentreport', 'Can change Unfallbericht'),
    ('delete_accidentreport', 'Can delete Unfallbericht'),
]


def create_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    content_type, _ = ContentType.objects.get_or_create(
        app_label='accident_report', model='accidentreport'
    )

    perms = []
    for codename, name in PERMISSIONS:
        perm, _ = Permission.objects.get_or_create(
            codename=codename,
            content_type=content_type,
            defaults={'name': name},
        )
        perms.append(perm)

    group, _ = Group.objects.get_or_create(name=GROUP_NAME)
    group.permissions.add(*perms)


def remove_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name=GROUP_NAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accident_report', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(create_group, remove_group),
    ]
