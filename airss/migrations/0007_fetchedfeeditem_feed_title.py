# Generated by Django 4.1.10 on 2024-04-30 15:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('airss', '0006_rssfeedsource_source_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='fetchedfeeditem',
            name='feed_title',
            field=models.TextField(default=''),
        ),
    ]
