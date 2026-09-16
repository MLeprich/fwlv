"""Bestätigte Bedeutungen (F, FC, HB, L0, A2E, DV) auf bestehende Installationen übertragen."""
from django.db import migrations


def forwards(apps, schema_editor):
    from dienstplan.defaults import ensure_default_codes
    ensure_default_codes(apps.get_model('dienstplan', 'DutyCode'))


class Migration(migrations.Migration):

    dependencies = [
        ('dienstplan', '0003_a2e_and_confirmed_codes'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
