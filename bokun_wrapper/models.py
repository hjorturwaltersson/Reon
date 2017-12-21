from django.db import models
from jsonfield import JSONField
from .api_sync_model_py import ApiSyncModel
from .get_data import get_availability as api_availability


class Vendor(models.Model):
    bokun_id = models.CharField(unique=True, max_length=1000)
    title = models.CharField(max_length=1000)
    json = JSONField()


class Place(models.Model):
    bokun_id = models.CharField(unique=True, max_length=1000, primary_key=True)
    title = models.CharField(max_length=1000)
    location = JSONField()
    json = JSONField()


class Product(models.Model):
    bokun_id = models.CharField(unique=True, max_length=1000, primary_key=True)
    title = models.CharField(max_length=1000)
    excerpt = models.CharField(max_length=1000)
    bookable_extras = JSONField(null=True)
    price = models.CharField(max_length=1000, null=True)
    photos = JSONField(null=True)
    vendor = models.ForeignKey(Vendor, null=True, on_delete=models.SET_NULL)
    external_id = models.CharField(max_length=1000)
    json = JSONField(null=True)
    pickup_places = models.ManyToManyField(Place, related_name='+', blank=True)
    dropoff_places = models.ManyToManyField(Place, related_name='+', blank=True)
    default_price_category_id = models.IntegerField(null=True)
    teenager_price_category_id = models.IntegerField(null=True)
    child_price_category_id = models.IntegerField(null=True)

    def get_availability(self, date):
        return api_availability(self.bokun_id, date)

    def __str__(self):
        return self.title


class FrontPageProduct(models.Model):
    bokun_product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL, related_name='+')
    return_product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL, related_name='+')
    bluelagoon_product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL, related_name='+')
    tagline = models.CharField(max_length=200)
    adult_price = models.IntegerField()
    teenager_price = models.IntegerField()

    def __str__(self):
        return self.bokun_product.title