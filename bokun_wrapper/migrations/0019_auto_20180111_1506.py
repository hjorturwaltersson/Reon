# Generated by Django 2.0 on 2018-01-11 15:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bokun_wrapper', '0018_crosssaleitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='frontpageproduct',
            name='max_people',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='frontpageproduct',
            name='min_people',
            field=models.IntegerField(default=0),
        ),
    ]
