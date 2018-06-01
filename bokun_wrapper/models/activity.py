from operator import itemgetter
import arrow

from django.core.cache import cache
from django.db import models
from jsonfield import JSONField

from ..utils import nearest
from .activity_property_mixin import ActivityPropertyMixin


extra_id_map = {
    'flight_delay_guarantee': ['flightdelayguarantee', 'delayguarantee', 'fld'],

    'child_seat_infant': ['childseat0-13kg', 'childseatinfant'],
    'child_seat_child': ['childseat14-36kg', 'childseatchild', 'childseat', 'childseatchildren'],

    'extra_baggage': ['extrabaggage'],
    'odd_size_baggage': ['oddsizebaggage', 'oddsizedbaggage'],
}


class InvalidStartTime(Exception):
    pass


class Activity(ActivityPropertyMixin, models.Model):
    external_id = models.CharField(max_length=255)

    title = models.CharField(max_length=255)
    excerpt = models.TextField(blank=True)

    bookable_extras = JSONField(default=[])
    photos = JSONField(default=[])

    vendor = models.ForeignKey('Vendor', null=True, on_delete=models.SET_NULL)

    pickup_places = models.ManyToManyField('Place', related_name='+', blank=True)
    dropoff_places = models.ManyToManyField('Place', related_name='+', blank=True)

    json = JSONField(default={})

    def get_availability(self, date):
        date = arrow.get(date)

        formatted_date = date.format('YYYY-MM-DD')

        cache_key = 'product:%s:availability:%s' % (self.id, formatted_date)

        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        from bokun_wrapper.get_data import bokun_api

        availabilities = bokun_api.get('/activity.json/%s/availabilities' % self.id, {
            'start': formatted_date,
            'end': date.shift(days=1).format('YYYY-MM-DD'),
            'includeSoldOut': True,
        }).json()

        # I don't trust Bokun to sort this properly:
        availabilities.sort(key=itemgetter('date', 'startTime'))

        def makeCategoryPrices(a):
            prices = a['pricesByCategory'].values()
            return {
                'ADULT': int(max(prices)),
                'CHILD': int(min(prices)),
            }

        data = [{
            'id': a['startTimeId'],
            'date': arrow.get(a['date'] / 1000).format('YYYY-MM-DD'),
            'time': a['startTime'],
            'available': 0 if (a['soldOut'] or a['unavailable']) else a['availabilityCount'],
            'categoryPrices': makeCategoryPrices(a),
            'extraPrices': {int(id): int(price) for id, price in a['extraPrices'].items()},
        } for a in availabilities]

        cache.set(cache_key, data, 60 * 10)  # Cache for 10 minutes

        return data

    def get_start_time_ids(self, date):
        return {arrow.get('%sT%s' % (a['date'], a['time'])).datetime: a['id']
                for a in self.get_availability(date)}

    def get_start_time_id(self, dt, strict=True):
        dt = arrow.get(dt).datetime

        st_dict = self.get_start_time_ids(dt)
        st_keys = st_dict.keys()

        try:
            return st_dict[dt]
        except KeyError:
            if strict:
                times = [arrow.get(t).format('HH:mm') for t in st_keys]
                raise InvalidStartTime('Start time be one of: %s' % ', '.join(times))

            return st_dict[nearest([k for k in st_keys if k > dt], dt)]

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
            print(self.id)
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

    class Meta:
        verbose_name_plural = 'Activities'
