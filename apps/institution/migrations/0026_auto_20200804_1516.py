# Generated by Django 2.2.13 on 2020-08-04 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('institution', '0025_institution_grondslag'),
    ]

    operations = [
        migrations.RenameField(
            model_name='institution',
            old_name='grondslag',
            new_name='grondslag_formeel',
        ),
        migrations.AddField(
            model_name='institution',
            name='grondslag_informeel',
            field=models.CharField(choices=[('uitvoering_overeenkomst', 'uitvoering_overeenkomst'), ('gerechtvaardigd_belang', 'gerechtvaardigd_belang'), ('wettelijke_verplichting', 'wettelijke_verplichting')], default='uitvoering_overeenkomst', max_length=254),
        ),
    ]
