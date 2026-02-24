"""
Step 1: Add DefectCategoryModel + temporary category_new FK field on Defect
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('defect_management', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DefectCategoryModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Zeitpunkt der Erstellung', verbose_name='Erstellt am')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Zeitpunkt der letzten Aenderung', verbose_name='Aktualisiert am')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Name')),
                ('icon', models.CharField(default='\u26a0\ufe0f', max_length=10, verbose_name='Icon')),
                ('color', models.CharField(blank=True, help_text="Tailwind-Farbklasse, z.B. 'red', 'blue'", max_length=20, verbose_name='Farbe')),
                ('description', models.TextField(blank=True, verbose_name='Beschreibung')),
                ('is_active', models.BooleanField(default=True, verbose_name='Aktiv')),
                ('sort_order', models.IntegerField(default=0, verbose_name='Sortierung')),
                ('app_label', models.CharField(blank=True, help_text="Django App-Label für Objekt-Lookup, z.B. 'vehicles'", max_length=50, verbose_name='App-Label')),
                ('model_name', models.CharField(blank=True, help_text="Django Model-Name für Objekt-Lookup, z.B. 'vehicle'", max_length=50, verbose_name='Model-Name')),
            ],
            options={
                'verbose_name': 'Mangel-Kategorie',
                'verbose_name_plural': 'Mangel-Kategorien',
                'ordering': ['sort_order', 'name'],
            },
        ),
        # Add temporary nullable FK field
        migrations.AddField(
            model_name='defect',
            name='category_new',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='defects_new',
                to='defect_management.defectcategorymodel',
                verbose_name='Kategorie (neu)',
            ),
        ),
    ]
