# Generated by Django 5.0 on 2023-12-21 10:34

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("django_peertube_runner_connector", "0002_video_basefilename"),
    ]

    operations = [
        migrations.AddField(
            model_name="runnerjob",
            name="domain",
            field=models.CharField(
                blank=True, help_text="Job domain", max_length=255, null=True
            ),
        ),
        migrations.AlterField(
            model_name="runnerjob",
            name="error",
            field=models.TextField(blank=True, help_text="Error message", null=True),
        ),
    ]
