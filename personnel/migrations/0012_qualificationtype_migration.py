# Generated manually for QualificationType conversion
import django.db.models.deletion
from django.db import migrations, models


def create_default_types(apps, schema_editor):
    """Create default qualification types from old TextChoices"""
    QualificationType = apps.get_model('personnel', 'QualificationType')

    default_types = [
        {'name': 'Lehrgang', 'abbreviation': 'LG', 'color': '#3B82F6', 'icon': '🎓', 'sort_order': 1},
        {'name': 'Zertifikat', 'abbreviation': 'CERT', 'color': '#10B981', 'icon': '📜', 'sort_order': 2},
        {'name': 'Führerschein/Lizenz', 'abbreviation': 'FS', 'color': '#F59E0B', 'icon': '🚗', 'sort_order': 3},
        {'name': 'Medizinische Untersuchung', 'abbreviation': 'MED', 'color': '#EF4444', 'icon': '🏥', 'sort_order': 4},
        {'name': 'Sicherheitsunterweisung', 'abbreviation': 'SU', 'color': '#8B5CF6', 'icon': '⚠️', 'sort_order': 5},
        {'name': 'Sonstiges', 'abbreviation': 'SONST', 'color': '#6B7280', 'icon': '📋', 'sort_order': 6},
    ]

    for type_data in default_types:
        QualificationType.objects.create(**type_data)


def convert_old_values(apps, schema_editor):
    """Convert old CharField values to ForeignKey references"""
    QualificationTemplate = apps.get_model('personnel', 'QualificationTemplate')
    Qualification = apps.get_model('personnel', 'Qualification')
    Training = apps.get_model('personnel', 'Training')
    QualificationType = apps.get_model('personnel', 'QualificationType')

    # Mapping from old TextChoices values to new type names
    type_mapping = {
        'course': 'Lehrgang',
        'cert': 'Zertifikat',
        'license': 'Führerschein/Lizenz',
        'medical': 'Medizinische Untersuchung',
        'safety': 'Sicherheitsunterweisung',
        'other': 'Sonstiges',
    }

    # Convert QualificationTemplate
    for template in QualificationTemplate.objects.all():
        old_value = template.qualification_type_old
        new_type_name = type_mapping.get(old_value, 'Sonstiges')
        new_type = QualificationType.objects.get(name=new_type_name)
        template.qualification_type_new = new_type
        template.save()

    # Convert Qualification
    for qual in Qualification.objects.all():
        old_value = qual.qualification_type_old
        new_type_name = type_mapping.get(old_value, 'Sonstiges')
        new_type = QualificationType.objects.get(name=new_type_name)
        qual.qualification_type_new = new_type
        qual.save()

    # Convert Training
    for training in Training.objects.all():
        old_value = training.training_type_old
        new_type_name = type_mapping.get(old_value, 'Sonstiges')
        new_type = QualificationType.objects.get(name=new_type_name)
        training.training_type_new = new_type
        training.save()


class Migration(migrations.Migration):

    dependencies = [
        ('personnel', '0011_dutyhourscategory_and_more'),
    ]

    operations = [
        # Step 1: Create QualificationType model
        migrations.CreateModel(
            name='QualificationType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='z.B. Lehrgang, Zertifikat, Führerschein/Lizenz', max_length=200, unique=True, verbose_name='Name')),
                ('abbreviation', models.CharField(blank=True, help_text='z.B. LG, CERT, FS', max_length=20, verbose_name='Abkürzung')),
                ('description', models.TextField(blank=True, verbose_name='Beschreibung')),
                ('color', models.CharField(default='#6366F1', help_text='Hex-Farbcode für Darstellung (z.B. #6366F1)', max_length=7, verbose_name='Farbe')),
                ('icon', models.CharField(default='🎓', help_text='Emoji-Icon für Darstellung', max_length=10, verbose_name='Icon')),
                ('is_active', models.BooleanField(default=True, verbose_name='Aktiv')),
                ('sort_order', models.IntegerField(default=0, help_text='Niedrigere Werte werden zuerst angezeigt', verbose_name='Sortierung')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Erstellt am')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Aktualisiert am')),
            ],
            options={
                'verbose_name': 'Qualifikationstyp',
                'verbose_name_plural': 'Qualifikationstypen',
                'ordering': ['sort_order', 'name'],
                'indexes': [models.Index(fields=['is_active', 'sort_order'], name='personnel_q_is_acti_0abcc4_idx')],
            },
        ),

        # Step 2: Create default types
        migrations.RunPython(create_default_types, reverse_code=migrations.RunPython.noop),

        # Step 3: Rename old fields to _old
        migrations.RenameField(
            model_name='qualificationtemplate',
            old_name='qualification_type',
            new_name='qualification_type_old',
        ),
        migrations.RenameField(
            model_name='qualification',
            old_name='qualification_type',
            new_name='qualification_type_old',
        ),
        migrations.RenameField(
            model_name='training',
            old_name='training_type',
            new_name='training_type_old',
        ),

        # Step 4: Add new ForeignKey fields (nullable for now)
        migrations.AddField(
            model_name='qualificationtemplate',
            name='qualification_type_new',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='templates_temp', to='personnel.qualificationtype', verbose_name='Typ'),
        ),
        migrations.AddField(
            model_name='qualification',
            name='qualification_type_new',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='qualifications_temp', to='personnel.qualificationtype', verbose_name='Typ'),
        ),
        migrations.AddField(
            model_name='training',
            name='training_type_new',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='trainings_temp', to='personnel.qualificationtype', verbose_name='Schulungstyp'),
        ),

        # Step 5: Convert old values to new
        migrations.RunPython(convert_old_values, reverse_code=migrations.RunPython.noop),

        # Step 6: Remove old fields
        migrations.RemoveField(
            model_name='qualificationtemplate',
            name='qualification_type_old',
        ),
        migrations.RemoveField(
            model_name='qualification',
            name='qualification_type_old',
        ),
        migrations.RemoveField(
            model_name='training',
            name='training_type_old',
        ),

        # Step 7: Rename new fields to final names
        migrations.RenameField(
            model_name='qualificationtemplate',
            old_name='qualification_type_new',
            new_name='qualification_type',
        ),
        migrations.RenameField(
            model_name='qualification',
            old_name='qualification_type_new',
            new_name='qualification_type',
        ),
        migrations.RenameField(
            model_name='training',
            old_name='training_type_new',
            new_name='training_type',
        ),

        # Step 8: Make fields NOT NULL and update related_name
        migrations.AlterField(
            model_name='qualificationtemplate',
            name='qualification_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='templates', to='personnel.qualificationtype', verbose_name='Typ'),
        ),
        migrations.AlterField(
            model_name='qualification',
            name='qualification_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='qualifications', to='personnel.qualificationtype', verbose_name='Typ'),
        ),
        migrations.AlterField(
            model_name='training',
            name='training_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='trainings', to='personnel.qualificationtype', verbose_name='Schulungstyp'),
        ),
    ]
