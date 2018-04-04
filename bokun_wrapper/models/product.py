from django.db import models
from jsonfield import JSONField


DIRECTION_CHOICES = (
    ('ANY', 'ANY'),
    ('KEF-RVK', 'KEF-RVK'),
    ('RVK-KEF', 'RVK-KEF'),
)

PRODUCT_TYPE_CHOICES = (
    ('ECO', 'Economy'),
    ('PRE', 'Premium'),
    ('PRI', 'Private'),
    ('LUX', 'Luxury'),
)


class Product(models.Model):
    bokun_product = models.ForeignKey('Activity', null=True, blank=True,
                                      on_delete=models.SET_NULL, related_name='+')
    return_product = models.ForeignKey('Activity', null=True, blank=True,
                                       on_delete=models.SET_NULL, related_name='+')
    discount_product = models.ForeignKey('Activity', null=True, blank=True,
                                         on_delete=models.SET_NULL, related_name='+')

    kind = models.CharField(max_length=3, choices=PRODUCT_TYPE_CHOICES,
                            db_column='type', default='ECO', db_index=True)

    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, default='ANY')

    tagline = models.CharField(max_length=200, default='')

    photo_path = models.CharField(max_length=200, default='')

    title = models.CharField(max_length=200, default='')

    ordering = models.IntegerField(default=0, db_index=True)

    min_people = models.IntegerField(default=0, db_index=True)
    max_people = models.IntegerField(default=0, db_index=True)

    @property
    def single_seat_booking(self):
        return self.kind in ['ECO', 'PRE']

    @property
    def _discount_product(self):
        return self.discount_product or self.bokun_product

    @property
    def description(self):
        return self.bokun_product.json['description']

    @property
    def excerpt(self):
        return self.bokun_product.json['excerpt']

    def __str__(self):
        if self.bokun_product:
            return self.bokun_product.title
        else:
            return 'untitled'

    class Meta:
        ordering = ['ordering', 'title']


class ProductBullet(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='bullets')

    icon = models.CharField(max_length=100)
    text = models.CharField(max_length=100)

    def __str__(self):
        return '%s - %s' % (self.icon, self.text)
