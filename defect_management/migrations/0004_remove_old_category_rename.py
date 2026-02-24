"""
Step 3: Remove old CharField category, rename category_new -> category
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('defect_management', '0003_seed_categories_migrate_defects'),
    ]

    operations = [
        # Remove old CharField
        migrations.RemoveField(
            model_name='defect',
            name='category',
        ),
        # Rename category_new -> category
        migrations.RenameField(
            model_name='defect',
            old_name='category_new',
            new_name='category',
        ),
        # Make it non-nullable and update related_name
        migrations.AlterField(
            model_name='defect',
            name='category',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='defects',
                to='defect_management.defectcategorymodel',
                verbose_name='Kategorie',
            ),
        ),
    ]
