# Generated by Django 2.0 on 2018-01-06 17:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bokun_wrapper', '0008_auto_20180106_1507'),
    ]

    operations = [
        migrations.AddField(
            model_name='frontpageproduct',
            name='luxury',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='frontpageproduct',
            name='private',
            field=models.BooleanField(default=False),
        ),
    ]
