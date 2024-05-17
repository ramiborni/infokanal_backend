# Generated by Django 4.1.10 on 2024-05-05 21:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('airss', '0009_fetchedfeeditem_rss_feed_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='fetchedfeeditem',
            name='is_rejected',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='fetchedfeeditem',
            name='is_summarized',
            field=models.BooleanField(default=False),
        ),
    ]
