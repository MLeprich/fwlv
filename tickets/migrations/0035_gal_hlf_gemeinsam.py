"""
GAL-HLF ist EIN Fahrzeug, das für beide Wachen fährt.

Die getrennten Felder personal_fw1_gal_hlf / personal_fw2_gal_hlf werden durch
ein gemeinsames Feld gal_hlf ersetzt. Übernahme: gesetzt, wenn es vorher bei
mindestens einer der beiden Wachen aktiv war.
"""
from django.db import migrations, models


def merge_gal_hlf(apps, schema_editor):
    InfoMonitor = apps.get_model('tickets', 'InfoMonitor')
    for m in InfoMonitor.objects.all():
        m.gal_hlf = bool(m.personal_fw1_gal_hlf) or bool(m.personal_fw2_gal_hlf)
        m.save(update_fields=['gal_hlf'])


def split_gal_hlf(apps, schema_editor):
    """Rückwärts: beide Wachen bekommen den gemeinsamen Wert."""
    InfoMonitor = apps.get_model('tickets', 'InfoMonitor')
    for m in InfoMonitor.objects.all():
        m.personal_fw1_gal_hlf = bool(m.gal_hlf)
        m.personal_fw2_gal_hlf = bool(m.gal_hlf)
        m.save(update_fields=['personal_fw1_gal_hlf', 'personal_fw2_gal_hlf'])


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0034_vehicle_freitext'),
    ]

    operations = [
        migrations.AddField(
            model_name='infomonitor',
            name='gal_hlf',
            field=models.BooleanField(default=False, verbose_name='GAL-HLF (beide Wachen)'),
        ),
        migrations.RunPython(merge_gal_hlf, split_gal_hlf),
        migrations.RemoveField(model_name='infomonitor', name='personal_fw1_gal_hlf'),
        migrations.RemoveField(model_name='infomonitor', name='personal_fw2_gal_hlf'),
    ]
