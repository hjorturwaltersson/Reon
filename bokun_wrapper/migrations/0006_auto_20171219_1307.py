# Generated by Django 2.0 on 2017-12-19 13:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bokun_wrapper', '0005_auto_20171214_1418'),
    ]

    operations = [
        migrations.CreateModel(
            name='FrontPageProduct',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tagline', models.CharField(max_length=200)),
                ('adult_price', models.IntegerField()),
                ('teenager_price', models.IntegerField()),
            ],
        ),
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.CharField(max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='frontpageproduct',
            name='bluelagoon_product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='bokun_wrapper.Product'),
        ),
        migrations.AddField(
            model_name='frontpageproduct',
            name='bokun_product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='bokun_wrapper.Product'),
        ),
        migrations.AddField(
            model_name='frontpageproduct',
            name='return_product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='bokun_wrapper.Product'),
        ),
    ]
