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

PRODUCT_TAGLINE_COLOR_CHOICES = (
    ('green', 'Green'),
    ('blue', 'Blue'),
    ('purple', 'Purple'),
    ('gold', 'Gold'),
)


class Product(models.Model):
    activity_inbound = models.ForeignKey('Activity', verbose_name='KEF-RVK',
                                         on_delete=models.CASCADE, related_name='+')
    activity_outbound = models.ForeignKey('Activity', verbose_name='RVK-KEF',
                                          on_delete=models.CASCADE, related_name='+')

    activity_inbound_rt = models.ForeignKey('Activity', verbose_name='KEF-RVK (round trip)',
                                            null=True, blank=True, on_delete=models.SET_NULL,
                                            related_name='+')
    activity_outbound_rt = models.ForeignKey('Activity', verbose_name='RVK-KEF (round trip)',
                                             null=True, blank=True, on_delete=models.SET_NULL,
                                             related_name='+')

    activity_inbound_hc = models.ForeignKey('Activity', verbose_name='KEF-RVK + HC',
                                            null=True, blank=True, on_delete=models.SET_NULL,
                                            related_name='+')
    activity_outbound_hc = models.ForeignKey('Activity', verbose_name='RVK-KEF + HC',
                                             null=True, blank=True, on_delete=models.SET_NULL,
                                             related_name='+')

    activity_inbound_hc_rt = models.ForeignKey('Activity', verbose_name='KEF-RVK + HC (round trip)',
                                               null=True, blank=True, on_delete=models.SET_NULL,
                                               related_name='+')
    activity_outbound_hc_rt = models.ForeignKey('Activity', verbose_name='RVK-KEF + HC (round trip)',
                                                null=True, blank=True, on_delete=models.SET_NULL,
                                                related_name='+')

    free_hotel_connection = models.BooleanField(default=False)

    kind = models.CharField(max_length=3, choices=PRODUCT_TYPE_CHOICES,
                            db_column='type', default='ECO', db_index=True)

    tagline = models.CharField(max_length=200, blank=True)
    tagline_color = models.CharField(max_length=10, default='green',
                                     choices=PRODUCT_TAGLINE_COLOR_CHOICES)

    link_url = models.CharField(max_length=255, blank=True)

    photo_path = models.CharField(max_length=200, blank=True)

    title = models.CharField(max_length=200, blank=True)

    excerpt = models.TextField(blank=True)

    ordering = models.IntegerField(default=0, db_index=True)

    min_people = models.IntegerField(default=0, db_index=True)
    max_people = models.IntegerField(default=0, db_index=True)

    def get_activity(self, outbound=False, hotel_connection=False, round_trip=False):
        hotel_connection = False if self.free_hotel_connection else hotel_connection

        def get(outbound, hotel_connection, round_trip):
            attr = 'activity_%s%s%s' % (
                'outbound' if outbound else 'inbound',
                '_hc' if hotel_connection else '',
                '_rt' if round_trip else '',
            )

            return getattr(self, attr)

        return (
            get(outbound, hotel_connection, round_trip) or
            get(outbound, hotel_connection, False) or
            get(outbound, False, False)
        )

    @property
    def activity_ids(self):
        return [
            self.activity_inbound_id,
            self.activity_outbound_id,
            self.activity_inbound_rt_id,
            self.activity_outbound_rt_id,
            self.activity_inbound_hc_id,
            self.activity_outbound_hc_id,
            self.activity_inbound_hc_rt_id,
            self.activity_outbound_hc_rt_id,
        ]

    @property
    def single_seat_booking(self):
        return self.kind in ['ECO', 'PRE']

    @property
    def description(self):
        return self.activity_inbound.json['description']

    def __str__(self):
        if self.activity_inbound:
            return self.activity_inbound.title
        else:
            return 'untitled'

    class Meta:
        ordering = ['ordering', 'title']


ICON_CHOICES = (
    ('airport', 'Airport'),
    ('arrow-small', 'arrow-Small'),
    ('back', 'Back'),
    ('baggage', 'Baggage'),
    ('burger', 'Burger'),
    ('bus', 'Bus'),
    ('terminal', 'Terminal'),
    ('child', 'Child'),
    ('close', 'Close'),
    ('dropdown', 'Dropdown'),
    ('edit', 'Edit'),
    ('flight-delay', 'Flight Delay'),
    ('hotel', 'Hotel'),
    ('info', 'Info'),
    ('minus', 'Minus'),
    ('odd-baggage', 'Odd Sized Baggage'),
    ('plus', 'Plus'),
    ('search', 'Search'),
    ('sport-baggage', 'Sport Baggage'),
    ('unknown', 'Unknown'),
)

class ProductBullet(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='bullets')

    icon = models.CharField(max_length=50, choices=ICON_CHOICES, blank=True)

    image = models.URLField(blank=True)

    text = models.CharField(max_length=100)

    def __str__(self):
        return '%s - %s' % (self.icon, self.text)
