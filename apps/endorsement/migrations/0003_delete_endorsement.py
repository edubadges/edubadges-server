# Generated manually to drop the Endorsement model and endorsement_endorsement table

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('endorsement', '0002_endorsement_rejection_reason'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Endorsement',
        ),
    ]
