# Generated migration for auto-verify functionality

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fragrances', '0018_trialpackprice'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='is_verified',
            field=models.BooleanField(default=True),
        ),
    ]
