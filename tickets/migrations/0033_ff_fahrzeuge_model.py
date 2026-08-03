# FF-Züge: "Im Anmarsch" entfernen + Freitext-Fahrzeuge in eigenes Modell
# (InfoMonitorFFFahrzeug) mit Freitext-Stärke überführen.

import django.db.models.deletion
from django.db import migrations, models


def copy_fahrzeuge(apps, schema_editor):
    """Bestehende ff_*_fahrzeuge-Strings in je einen FF-Fahrzeug-Eintrag überführen."""
    InfoMonitor = apps.get_model('tickets', 'InfoMonitor')
    FF = apps.get_model('tickets', 'InfoMonitorFFFahrzeug')
    mapping = [
        ('sterkrade', 'ff_sterkrade_fahrzeuge'),
        ('mitte', 'ff_mitte_fahrzeuge'),
        ('sued', 'ff_sued_fahrzeuge'),
        ('koe', 'ff_koe_fahrzeuge'),
    ]
    for m in InfoMonitor.objects.all():
        for zug, field in mapping:
            val = (getattr(m, field, '') or '').strip()
            if val:
                FF.objects.create(monitor=m, zug=zug, fahrzeug=val, staerke='', position=0)


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0032_personal_ergaenzung_boolean'),
    ]

    operations = [
        # 1. Neues Modell anlegen
        migrations.CreateModel(
            name='InfoMonitorFFFahrzeug',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zug', models.CharField(choices=[('sterkrade', 'FF Sterkrade'), ('mitte', 'FF Mitte'), ('sued', 'FF Süd'), ('koe', 'FF KÖ')], max_length=20, verbose_name='Zug')),
                ('fahrzeug', models.CharField(blank=True, default='', max_length=100, verbose_name='Fahrzeug')),
                ('staerke', models.CharField(blank=True, default='', max_length=50, verbose_name='Fahrzeugstärke')),
                ('position', models.PositiveIntegerField(default=0, verbose_name='Position')),
                ('monitor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ff_fahrzeuge', to='tickets.infomonitor', verbose_name='Info-Monitor')),
            ],
            options={
                'verbose_name': 'Info-Monitor FF-Fahrzeug',
                'verbose_name_plural': 'Info-Monitor FF-Fahrzeuge',
                'ordering': ['zug', 'position'],
            },
        ),
        # 2. Bestehende Freitext-Fahrzeuge übernehmen (Altfelder existieren hier noch)
        migrations.RunPython(copy_fahrzeuge, migrations.RunPython.noop),
        # 3. Altfelder entfernen
        migrations.RemoveField(model_name='infomonitor', name='ff_koe_fahrzeuge'),
        migrations.RemoveField(model_name='infomonitor', name='ff_mitte_fahrzeuge'),
        migrations.RemoveField(model_name='infomonitor', name='ff_sterkrade_fahrzeuge'),
        migrations.RemoveField(model_name='infomonitor', name='ff_sued_fahrzeuge'),
        # 4. Status-Choices ohne "Im Anmarsch"
        migrations.AlterField(
            model_name='infomonitor',
            name='ff_koe_status',
            field=models.CharField(choices=[('einsatzbereit', 'Einsatzbereit'), ('nicht_einsatzbereit', 'Nicht Einsatzbereit')], default='einsatzbereit', max_length=25, verbose_name='FF KÖ'),
        ),
        migrations.AlterField(
            model_name='infomonitor',
            name='ff_mitte_status',
            field=models.CharField(choices=[('einsatzbereit', 'Einsatzbereit'), ('nicht_einsatzbereit', 'Nicht Einsatzbereit')], default='einsatzbereit', max_length=25, verbose_name='FF Mitte'),
        ),
        migrations.AlterField(
            model_name='infomonitor',
            name='ff_sterkrade_status',
            field=models.CharField(choices=[('einsatzbereit', 'Einsatzbereit'), ('nicht_einsatzbereit', 'Nicht Einsatzbereit')], default='einsatzbereit', max_length=25, verbose_name='FF Sterkrade'),
        ),
        migrations.AlterField(
            model_name='infomonitor',
            name='ff_sued_status',
            field=models.CharField(choices=[('einsatzbereit', 'Einsatzbereit'), ('nicht_einsatzbereit', 'Nicht Einsatzbereit')], default='einsatzbereit', max_length=25, verbose_name='FF Süd'),
        ),
    ]
