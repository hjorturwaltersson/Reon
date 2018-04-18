# Generated by Django 2.0.3 on 2018-04-04 11:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bokun_wrapper', '0027_auto_20180328_1459'),
    ]

    operations = [
        migrations.CreateModel(
            name='FrontPageProductBullet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('icon', models.CharField(max_length=100)),
                ('text', models.CharField(max_length=100)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bullets', to='bokun_wrapper.FrontPageProduct')),
            ],
        ),
    ]