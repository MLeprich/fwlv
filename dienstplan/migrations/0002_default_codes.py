"""
Vorbelegung der Dienstcodes aus dem ersten Export (Fachabteilung Führungsdienst).
Die Bedeutungen sind aus dem Muster abgeleitet (je Tag genau ein A1, A2, B,
C-Dienst und Lagedienst) und mit verified=False markiert – bitte in der
Code-Tabelle prüfen.
"""
from django.db import migrations

def forwards(apps, schema_editor):
    from dienstplan.defaults import ensure_default_codes
    ensure_default_codes(apps.get_model('dienstplan', 'DutyCode'))


class Migration(migrations.Migration):

    dependencies = [
        ('dienstplan', '0001_dienstplan'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
