# Generated by Django 4.1.10 on 2024-05-09 14:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('airss', '0015_alter_fetchedfeeditem_feed_content'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fetchedfeeditem',
            name='feed_content',
            field=models.TextField(blank=True, default=''),
        ),
    ]
