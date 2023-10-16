# Generated by Django 3.2.21 on 2023-10-16 14:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("django_peertube_runner_connector", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="video",
            name="baseFilename",
            field=models.CharField(
                blank=True,
                help_text="File used for new files related to the video",
                max_length=255,
                null=True,
            ),
        ),
    ]
