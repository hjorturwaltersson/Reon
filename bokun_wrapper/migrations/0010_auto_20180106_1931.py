# Generated by Django 2.0 on 2018-01-06 19:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bokun_wrapper', '0009_auto_20180106_1721'),
    ]

    operations = [
        migrations.AddField(
            model_name='frontpageproduct',
            name='photo_path',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='place',
            name='type',
            field=models.CharField(choices=[('hotel', 'Hotel'), ('terminal', 'Terminal'), ('airport', 'Airport'), ('other', 'Other')], default='hotel', max_length=200),
        ),
    ]