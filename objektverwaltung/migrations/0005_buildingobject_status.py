from django.db import migrations, models


def is_active_to_status(apps, schema_editor):
    BuildingObject = apps.get_model('objektverwaltung', 'BuildingObject')
    BuildingObject.objects.filter(is_active=False).update(status='inactive')


def status_to_is_active(apps, schema_editor):
    BuildingObject = apps.get_model('objektverwaltung', 'BuildingObject')
    BuildingObject.objects.exclude(status='active').update(is_active=False)


class Migration(migrations.Migration):

    dependencies = [
        ('objektverwaltung', '0004_pruefungen_generalisiert'),
    ]

    operations = [
        migrations.AddField(
            model_name='buildingobject',
            name='status',
            field=models.CharField(
                choices=[('active', 'Aktiv'), ('planned', 'In Planung'), ('inactive', 'Inaktiv'),
                         ('for_deletion', 'Zum Löschen vorgemerkt')],
                default='active', max_length=20, verbose_name='Status'),
        ),
        migrations.RunPython(is_active_to_status, status_to_is_active),
        migrations.RemoveField(
            model_name='buildingobject',
            name='is_active',
        ),
    ]
