# Generated by Django 2.0.3 on 2018-04-16 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bokun_wrapper', '0033_product_link_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='productbullet',
            name='image',
            field=models.URLField(blank=True),
        ),
        migrations.AlterField(
            model_name='productbullet',
            name='icon',
            field=models.CharField(blank=True, choices=[('airport', 'Airport'), ('arrow-small', 'arrow-Small'), ('back', 'Back'), ('baggage', 'Baggage'), ('burger', 'Burger'), ('bus', 'Bus'), ('terminal', 'Terminal'), ('child', 'Child'), ('close', 'Close'), ('dropdown', 'Dropdown'), ('edit', 'Edit'), ('flight-delay', 'Flight Delay'), ('hotel', 'Hotel'), ('info', 'Info'), ('minus', 'Minus'), ('odd-baggage', 'Odd Sized Baggage'), ('plus', 'Plus'), ('search', 'Search'), ('sport-baggage', 'Sport Baggage'), ('unknown', 'Unknown')], max_length=50),
        ),
    ]
