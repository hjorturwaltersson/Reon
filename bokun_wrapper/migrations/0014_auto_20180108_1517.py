# Generated by Django 2.0 on 2018-01-08 15:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bokun_wrapper', '0013_place_ordering'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='place',
            options={'ordering': ['ordering', 'title']},
        ),
    ]
