# Generated by Django 4.1.10 on 2024-05-12 03:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('airss', '0017_alter_rssmodulesettings_rss_module'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fetchedfeeditem',
            name='image_url',
            field=models.TextField(blank=True, default=''),
        ),
    ]
