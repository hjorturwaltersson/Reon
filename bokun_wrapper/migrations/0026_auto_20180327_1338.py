# Generated by Django 2.0 on 2018-03-27 13:38

from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('bokun_wrapper', '0025_auto_20180323_1612'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='bokun_id',
            new_name='id',
        ),
        migrations.AlterField(
            model_name='product',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),

        migrations.RenameField(
            model_name='place',
            old_name='bokun_id',
            new_name='id',
        ),
        migrations.AlterField(
            model_name='place',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),

        migrations.RenameField(
            model_name='crosssaleitem',
            old_name='bokun_id',
            new_name='id',
        ),
        migrations.AlterField(
            model_name='crosssaleitem',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),

        migrations.AlterField(
            model_name='place',
            name='title',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='product',
            name='excerpt',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='external_id',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='product',
            name='title',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='bokun_id',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='title',
            field=models.CharField(max_length=255),
        ),
    ]
