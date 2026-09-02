from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def fill_building_and_type(apps, schema_editor):
    InspectionReport = apps.get_model('objektverwaltung', 'InspectionReport')
    for report in InspectionReport.objects.select_related('depot').all():
        if report.depot_id:
            report.building_id = report.depot.building_id
            report.inspection_type = 'fsd'
            report.save(update_fields=['building', 'inspection_type'])


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('objektverwaltung', '0003_feuerwehrschluesseldepot'),
    ]

    operations = [
        # --- Prüfbericht generalisieren ---------------------------------
        migrations.RenameModel(old_name='FSDInspectionReport', new_name='InspectionReport'),
        migrations.AlterModelOptions(
            name='inspectionreport',
            options={'ordering': ['-inspection_date', '-created_at'],
                     'verbose_name': 'Prüfbericht', 'verbose_name_plural': 'Prüfberichte'},
        ),
        migrations.AlterField(
            model_name='inspectionreport', name='depot',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='inspection_reports', to='objektverwaltung.firekeydepot',
                                    verbose_name='Schlüsseldepot'),
        ),
        migrations.AddField(
            model_name='inspectionreport', name='building',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='inspection_reports', to='objektverwaltung.buildingobject',
                                    verbose_name='Objekt'),
        ),
        migrations.AddField(
            model_name='inspectionreport', name='inspection_type',
            field=models.CharField(choices=[('fsd', 'Feuerwehrschlüsseldepot'), ('bmz', 'Brandmeldezentrale'),
                                            ('loeschanlage', 'Löschanlage')],
                                   default='fsd', max_length=20, verbose_name='Prüfungsart'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='inspectionreport', name='fire_alarm_panel',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='inspection_reports', to='objektverwaltung.firealarmpanel',
                                    verbose_name='Brandmeldezentrale'),
        ),
        migrations.AddField(
            model_name='inspectionreport', name='suppression_system',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='inspection_reports', to='objektverwaltung.firesuppressionsystem',
                                    verbose_name='Löschanlage'),
        ),
        migrations.RunPython(fill_building_and_type, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='inspectionreport', name='building',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                    related_name='inspection_reports', to='objektverwaltung.buildingobject',
                                    verbose_name='Objekt'),
        ),

        # --- BMZ prüfbar -------------------------------------------------
        migrations.AddField(
            model_name='firealarmpanel', name='inspection_interval_months',
            field=models.PositiveSmallIntegerField(default=12, verbose_name='Prüfintervall (Monate)'),
        ),
        migrations.AddField(
            model_name='firealarmpanel', name='last_inspection',
            field=models.DateField(blank=True, null=True, verbose_name='Letzte Prüfung'),
        ),
        migrations.AddField(
            model_name='firealarmpanel', name='next_inspection',
            field=models.DateField(blank=True, null=True,
                                   help_text='Wird aus letzter Prüfung (bzw. Einbaudatum) und Intervall berechnet',
                                   verbose_name='Nächste Prüfung'),
        ),

        # --- Löschanlage prüfbar ----------------------------------------
        migrations.AddField(
            model_name='firesuppressionsystem', name='inspection_interval_months',
            field=models.PositiveSmallIntegerField(default=12, verbose_name='Prüfintervall (Monate)'),
        ),
        migrations.AlterField(
            model_name='firesuppressionsystem', name='next_inspection',
            field=models.DateField(blank=True, null=True,
                                   help_text='Wird aus letzter Prüfung (bzw. Einbaudatum) und Intervall berechnet',
                                   verbose_name='Nächste Prüfung'),
        ),
    ]
