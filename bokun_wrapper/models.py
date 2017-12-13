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
    summary = models.CharField(max_length=1000)
    price = models.CharField(max_length=1000)
    photos = JSONField(null=True)
    vendor = models.ForeignKey(Vendor, null=True, on_delete=models.SET_NULL)
    external_id = models.CharField(max_length=1000)
    json = JSONField(null=True)
    pickup_places = models.ManyToManyField(Place, related_name='+', blank=True)
    dropoff_places = models.ManyToManyField(Place, related_name='+', blank=True)

    def get_availability(self, date):
        return api_availability(self.bokun_id, date)

