from django.db import models
from jsonfield import JSONField
from .api_sync_model_py import ApiSyncModel
from .get_data import get_availability as api_availability

TYPE_CHOICES = (
    ("hotel", "Hotel"),
    ("terminal", "Terminal"),
    ("airport", "Airport"),
    ("other", "Other")
)


class Vendor(models.Model):
    bokun_id = models.CharField(unique=True, max_length=1000)
    title = models.CharField(max_length=1000)
    json = JSONField()


class Place(models.Model):
    bokun_id = models.CharField(unique=True, max_length=1000, primary_key=True)
    title = models.CharField(max_length=1000)
    location = JSONField()
    json = JSONField()
    type = models.CharField(choices=TYPE_CHOICES, max_length=200, default="hotel")
    ordering = models.IntegerField(default=0)


    def __str__(self):
        return self.title

    class Meta:
        ordering = ['ordering', 'title']


class Product(models.Model):
    bokun_id = models.CharField(unique=True, max_length=1000, primary_key=True)
    title = models.CharField(max_length=1000)
    excerpt = models.CharField(max_length=1000, null=True)
    bookable_extras = JSONField(null=True)
    price = models.CharField(max_length=1000, null=True)
    photos = JSONField(null=True, blank=True)
    vendor = models.ForeignKey(Vendor, null=True, on_delete=models.SET_NULL)
    external_id = models.CharField(max_length=1000)
    json = JSONField(null=True)
    pickup_places = models.ManyToManyField(Place, related_name='+', blank=True)
    dropoff_places = models.ManyToManyField(Place, related_name='+', blank=True)
    default_price_category_id = models.IntegerField(null=True)
    child_price_category_id = models.IntegerField(null=True)
    flight_delay_id = models.IntegerField(null=True)
    flight_delay_question_id = models.IntegerField(null=True)
    odd_size_id = models.IntegerField(null=True)
    extra_baggage_id = models.IntegerField(null=True)
    child_seat_infant_id = models.IntegerField(null=True)
    child_seat_child_id = models.IntegerField(null=True)

    def get_availability(self, date):
        return api_availability(self.bokun_id, date)

    def __str__(self):
        return self.title


class FrontPageProduct(models.Model):
    bokun_product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    return_product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    discount_product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    tagline = models.CharField(max_length=200, default="")
    adult_price = models.IntegerField(default=0)
    child_price = models.IntegerField(default=0)
    adult_price_round_trip = models.IntegerField(default=0)
    child_price_round_trip = models.IntegerField(default=0)
    private = models.BooleanField(default=False)
    luxury = models.BooleanField(default=False)
    photo_path = models.CharField(max_length=200, default="")
    title = models.CharField(max_length=200, default="")
    ordering = models.IntegerField(default=0)
    min_people = models.IntegerField(default=0)
    max_people = models.IntegerField(default=0)

    def __str__(self):
        if self.bokun_product:
            return self.bokun_product.title
        else:
            return "untitled"

    class Meta:
        ordering = ['ordering', 'title']


class CrossSaleItem(models.Model):
    bokun_id = models.CharField(unique=True, max_length=1000, primary_key=True)
    json = JSONField(null=True, blank=True)

    adult_category_id = models.IntegerField(default=0)
    teenager_category_id = models.IntegerField(default=0)
    child_category_id = models.IntegerField(default=0)

    earphone_id = models.IntegerField(default=0)
    jacket_id = models.IntegerField(default=0)
    jacket_question_id = models.IntegerField(default=0)
    boots_id = models.IntegerField(default=0)
    boots_question_id = models.IntegerField(default=0)
    lunch_id = models.IntegerField(default=0)
    lunch_question_id = models.IntegerField(default=0)
    extra_person_id = models.IntegerField(default=0)