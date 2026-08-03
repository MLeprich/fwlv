"""
LZ-RTW-Felder (personal_fw1_5_rtw / personal_fw2_5_rtw) von Freitext (CharField)
auf Verfügbar-Checkbox (BooleanField) umstellen – mit Datenerhalt.

Postgres kann varchar nicht automatisch nach boolean casten, daher der Umweg
über ein temporäres Textfeld: umbenennen -> neues Boolean anlegen -> Werte
konvertieren -> Textfeld entfernen.
"""
from django.db import migrations, models


TRUTHY = {'ja', 'yes', 'y', '1', 'true', 'wahr', 'x', 'verfügbar', 'verfuegbar', 'vorhanden'}


def txt_to_bool(apps, schema_editor):
    InfoMonitor = apps.get_model('tickets', 'InfoMonitor')
    for m in InfoMonitor.objects.all():
        v1 = (m.personal_fw1_5_rtw_txt or '').strip().lower()
        v2 = (m.personal_fw2_5_rtw_txt or '').strip().lower()
        m.personal_fw1_5_rtw = v1 in TRUTHY
        m.personal_fw2_5_rtw = v2 in TRUTHY
        m.save(update_fields=['personal_fw1_5_rtw', 'personal_fw2_5_rtw'])


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0030_mappeanleitung_pdf_datei_and_more'),
    ]

    operations = [
        migrations.RenameField('infomonitor', 'personal_fw1_5_rtw', 'personal_fw1_5_rtw_txt'),
        migrations.RenameField('infomonitor', 'personal_fw2_5_rtw', 'personal_fw2_5_rtw_txt'),
        migrations.AddField(
            model_name='infomonitor',
            name='personal_fw1_5_rtw',
            field=models.BooleanField(default=False, verbose_name='FW1 LZ RTW verfügbar'),
        ),
        migrations.AddField(
            model_name='infomonitor',
            name='personal_fw2_5_rtw',
            field=models.BooleanField(default=False, verbose_name='FW2 LZ RTW verfügbar'),
        ),
        migrations.RunPython(txt_to_bool, migrations.RunPython.noop),
        migrations.RemoveField('infomonitor', 'personal_fw1_5_rtw_txt'),
        migrations.RemoveField('infomonitor', 'personal_fw2_5_rtw_txt'),
    ]
