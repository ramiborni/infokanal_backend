# Generated by Django 4.1.10 on 2024-04-27 02:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('airss', '0004_rssfeedsource_rss_module'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rssfeedsource',
            name='rss_module',
        ),
    ]