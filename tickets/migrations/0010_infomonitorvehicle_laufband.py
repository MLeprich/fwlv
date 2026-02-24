"""
Migration 0010: InfoMonitorVehicle model + Laufband fields
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0009_personal_freifeld_und_dienst_checkboxen'),
        ('vehicles', '0014_vehicle_bereich'),
    ]

    operations = [
        # Neues Model InfoMonitorVehicle
        migrations.CreateModel(
            name='InfoMonitorVehicle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveIntegerField(default=0, verbose_name='Position')),
                ('monitor', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='monitor_vehicles',
                    to='tickets.infomonitor',
                    verbose_name='Info-Monitor',
                )),
                ('fahrzeug_ad', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='+',
                    to='vehicles.vehicle',
                    verbose_name='Außer Dienst',
                )),
                ('ersetzt_mit', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='+',
                    to='vehicles.vehicle',
                    verbose_name='Ersetzt mit',
                )),
            ],
            options={
                'verbose_name': 'Info-Monitor Fahrzeug',
                'verbose_name_plural': 'Info-Monitor Fahrzeuge',
                'ordering': ['position'],
            },
        ),
        # Laufband-Felder auf InfoMonitor
        migrations.AddField(
            model_name='infomonitor',
            name='laufband_text',
            field=models.TextField(blank=True, default='', verbose_name='Laufband-Text'),
        ),
        migrations.AddField(
            model_name='infomonitor',
            name='laufband_geschwindigkeit',
            field=models.PositiveIntegerField(default=20, help_text='Sekunden pro Durchlauf (5-60)', verbose_name='Laufband-Geschwindigkeit'),
        ),
    ]
