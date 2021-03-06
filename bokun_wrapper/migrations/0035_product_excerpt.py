# Generated by Django 2.0.3 on 2018-05-02 15:08

from django.db import migrations, models


def forwards_func(apps, schema_editor):
    Product = apps.get_model('bokun_wrapper', 'Product')

    for p in Product.objects.using(schema_editor.connection.alias).all():
        p.excerpt = p.activity_inbound.json['excerpt'] or ''
        p.save()


class Migration(migrations.Migration):

    dependencies = [
        ('bokun_wrapper', '0034_auto_20180416_1217'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='excerpt',
            field=models.TextField(blank=True),
        ),

        migrations.RunPython(forwards_func),
    ]
