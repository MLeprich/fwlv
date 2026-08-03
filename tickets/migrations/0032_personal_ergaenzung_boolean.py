"""
Ergänzung-Felder (personal_fw1_ergaenzung / personal_fw2_ergaenzung) von
Freitext (CharField) auf Checkbox (BooleanField) umstellen – mit Datenerhalt.

Wie 0031: Postgres kann varchar nicht automatisch nach boolean casten, daher der
Umweg über ein temporäres Textfeld.
"""
from django.db import migrations, models


TRUTHY = {'ja', 'yes', 'y', '1', 'true', 'wahr', 'x', 'vorhanden'}


def txt_to_bool(apps, schema_editor):
    InfoMonitor = apps.get_model('tickets', 'InfoMonitor')
    for m in InfoMonitor.objects.all():
        v1 = (m.personal_fw1_ergaenzung_txt or '').strip().lower()
        v2 = (m.personal_fw2_ergaenzung_txt or '').strip().lower()
        m.personal_fw1_ergaenzung = v1 in TRUTHY
        m.personal_fw2_ergaenzung = v2 in TRUTHY
        m.save(update_fields=['personal_fw1_ergaenzung', 'personal_fw2_ergaenzung'])


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0031_personal_lz_rtw_boolean'),
    ]

    operations = [
        migrations.RenameField('infomonitor', 'personal_fw1_ergaenzung', 'personal_fw1_ergaenzung_txt'),
        migrations.RenameField('infomonitor', 'personal_fw2_ergaenzung', 'personal_fw2_ergaenzung_txt'),
        migrations.AddField(
            model_name='infomonitor',
            name='personal_fw1_ergaenzung',
            field=models.BooleanField(default=False, verbose_name='FW1 Ergänzung'),
        ),
        migrations.AddField(
            model_name='infomonitor',
            name='personal_fw2_ergaenzung',
            field=models.BooleanField(default=False, verbose_name='FW2 Ergänzung'),
        ),
        migrations.RunPython(txt_to_bool, migrations.RunPython.noop),
        migrations.RemoveField('infomonitor', 'personal_fw1_ergaenzung_txt'),
        migrations.RemoveField('infomonitor', 'personal_fw2_ergaenzung_txt'),
    ]
