from django.db import models
from jsonfield import JSONField
from .api_sync_model_py import ApiSyncModel


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
    vendor_id = models.IntegerField()
    title = models.CharField(max_length=1000)
    location = JSONField()
    json = JSONField()
    type = models.CharField(choices=TYPE_CHOICES, max_length=200, default="hotel")
    ordering = models.IntegerField(default=0)


    def __str__(self):
        return self.title

    class Meta:
        ordering = ['ordering', 'title']


extra_id_map = {
    'flight_delay_guarantee': ['flightdelayguarantee', 'delayguarantee', 'fld'],

    'child_seat_infant': ['childseat0-13kg', 'childseatinfant'],
    'child_seat_child': ['childseat14-36kg', 'childseatchild', 'childseat', 'childseatchildren'],

    'extra_baggage': ['extrabaggage'],
    'odd_size_baggage': ['oddsizebaggage', 'oddsizedbaggage'],
}

class Product(models.Model):
    bokun_id = models.CharField(unique=True, max_length=1000, primary_key=True)
    external_id = models.CharField(max_length=1000)

    title = models.CharField(max_length=1000)
    excerpt = models.CharField(max_length=1000, null=True)

    bookable_extras = JSONField(null=True)
    photos = JSONField(null=True, blank=True)

    vendor = models.ForeignKey(Vendor, null=True, on_delete=models.SET_NULL)

    pickup_places = models.ManyToManyField(Place, related_name='+', blank=True)
    dropoff_places = models.ManyToManyField(Place, related_name='+', blank=True)

    json = JSONField(null=True)

    @property
    def price_categories(self):
        return self.json['pricingCategories']

    @property
    def default_price_category(self):
        return next(filter(lambda c: c['defaultCategory'], self.price_categories), None)

    @property
    def default_price_category_id(self):
        return self.default_price_category['id']

    @property
    def child_price_category(self):
        try:
            return next(filter(lambda c: 'CHILD' in (c['ticketCategory'] + c['title']).upper(), self.price_categories), None)
        except IndexError:
            return self.default_price_category

    @property
    def child_price_category_id(self):
        return self.child_price_category['id']

    @property
    def extras(self):
        def find_extra(ext_ids):
            return next(filter(
                lambda e: e['externalId'].lower() in ext_ids, self.bookable_extras), None)

        return {key: find_extra(ext_ids) for key, ext_ids in extra_id_map.items()}

    @property
    def flight_delay_id(self):
        try:
            return self.extras['flight_delay_guarantee']['id']
        except:
            print(self.bokun_id)
            raise

    @property
    def flight_delay_question_id(self):
        return self.extras['flight_delay_guarantee']['questions'][0]['id']

    @property
    def extra_baggage_id(self):
        return self.extras['extra_baggage']['id']

    @property
    def odd_size_id(self):
        return self.extras['odd_size_baggage']['id']

    @property
    def child_seat_child_id(self):
        return self.extras['child_seat_child']['id']

    @property
    def child_seat_infant_id(self):
        return self.extras['child_seat_infant']['id']

    def __str__(self):
        return self.title


DIRECTION_CHOICES = (
    ('ANY', 'ANY'),
    ('KEF-RVK', 'KEF-RVK'),
    ('RVK-KEF', 'RVK-KEF'),
)


class FrontPageProduct(models.Model):
    bokun_product = models.ForeignKey(Product, null=True, blank=True,
                                      on_delete=models.SET_NULL, related_name='+')
    return_product = models.ForeignKey(Product, null=True, blank=True,
                                       on_delete=models.SET_NULL, related_name='+')
    discount_product = models.ForeignKey(Product, null=True, blank=True,
                                         on_delete=models.SET_NULL, related_name='+')

    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, default='ANY')

    tagline = models.CharField(max_length=200, default="")

    private = models.BooleanField(default=False)
    luxury = models.BooleanField(default=False)
    photo_path = models.CharField(max_length=200, default="")

    title = models.CharField(max_length=200, default="")

    ordering = models.IntegerField(default=0)

    min_people = models.IntegerField(default=0)
    max_people = models.IntegerField(default=0)

    @property
    def _discount_product(self):
        return self.discount_product or self.bokun_product

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


class RequestLog(models.Model):
    url = models.URLField(null=True, blank=True)
    incoming_body = JSONField(null=True, blank=True)
    outgoing_body = JSONField(null=True, blank=True)
    bokun_response = JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
