# Generated by Django 4.1.10 on 2024-05-06 03:27

import datetime
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('airss', '0010_fetchedfeeditem_is_rejected_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='fetchedfeeditem',
            name='pub_date',
            field=models.DateTimeField(auto_created=datetime.datetime(2024, 5, 6, 3, 27, 8, 465418), auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]