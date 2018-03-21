import uuid

from datetime import time
import arrow

from .bokun_api import BokunApi, BokunApiException


def parse_time_str(tstr):
    return time(*[int(t) for t in tstr.split(':')])


class Cart:
    def __init__(self, api=None, session_id=None):
        self.api = BokunApi() if api is None else api

        if session_id is None:
            self.session_id = uuid.uuid4()

        self._state = self.api.get('/shopping-cart.json/session/%s' % self.session_id).json()

        self._reservation_state = {}

    def add_activity(
        self,
        activity_id,
        start_date,
        start_time,
        strict_time=True,
        adults=1,
        children=0,
        pickup_place_id=None,
        dropoff_place_id=None,
        pickup_place_description=None,
        dropoff_place_description=None,
    ):
        formatted_date = arrow.get(start_date).format('YYYY-MM-DD')

        activity_data = self.api.get('/activity.json/%s' % activity_id).json()
        activity_availabilities = self.api.get('/activity.json/%s/availabilities' % activity_id, {
            'start': formatted_date,
            'end': formatted_date,
            'includeSoldOut': True,
        }).json()

        avail_start_times = {a['startTime']: a['startTimeId'] for a in activity_availabilities}

        try:
            start_time_id = avail_start_times[start_time]
        except KeyError:
            if strict_time:
                raise self.CartException(
                    'Invalid start_time. Must be one of: %s' % ', '.join(
                        avail_start_times.keys()))

            start_time = parse_time_str(start_time)
            avail_times = {parse_time_str(tstr): id for tstr, id in avail_start_times.items()}

            for t, id in avail_times.items():
                if start_time >= t:
                    start_time_id = id
                    break

        adult_pricing_category_id = None
        child_pricing_category_id = None
        for cat in activity_data['pricingCategories']:
            if cat['defaultCategory']:
                adult_pricing_category_id = cat['id']
                continue

            if 'CHILD' in (cat['ticketCategory'] + cat['title']).upper():
                child_pricing_category_id = cat['id']
                continue

        if not child_pricing_category_id:
            child_pricing_category_id = adult_pricing_category_id

        res = self.api.post('/shopping-cart.json/session/%s/activity' % self.session_id, {
            'activityId': activity_id,
            'startTimeId': start_time_id,
            'pickupPlaceId': pickup_place_id,
            'pickupPlaceDescription': pickup_place_description,
            'dropoffPlaceId': dropoff_place_id,
            'dropoffPlaceDescription': dropoff_place_description,
            'date': formatted_date,
            'pricingCategoryBookings': [{
                'pricingCategoryId': adult_pricing_category_id,
                'extras': [],
            } for _ in range(adults)] + [{
                'pricingCategoryId': child_pricing_category_id,
                'extras': [],
            } for _ in range(children)]
        }).json()

        try:
            error_message = res['message']
        except KeyError:
            self._state = res
        else:
            raise self.CartException('Failed to add activity to cart. Reason: %s' % error_message)

        return self

    def _merge_booking_fields(self, body, fields):
        if fields is not None:
            body.update({
                'bookingFields': [{
                    'name': key,
                    'value': value,
                } for key, value in fields.items()]
            })

    def reserve(self,
                answers=None,
                fields=None):
        body = {}

        self._merge_booking_fields(body, fields)

        if answers is not None:
            body.update({
                'answers': {
                    'answers': [{
                        'type': key,
                        'answer': value,
                    } for key, value in answers.items()]
                }
            })

        res = self.api.post('/booking.json/guest/%s/reserve' % self.session_id, body)

        self._reservation_state = res.json()

        return self

    def confirm(self,
                fields=None,
                mark_paid=False,
                reference_id=None,
                payment_reference_id=None,
                send_customer_notification=True):
        if self.booking_id is None:
            raise self.CartException(
                'Cannot confirm a booking that has not been reserved (bookingId missing)')

        body = {
            'externalBookingReference': reference_id,
        }

        self._merge_booking_fields(body, fields)

        if mark_paid:
            body.update({
                'payment': {
                    'amount': self.totalAmount,
                    'currency': self.currency,
                    'paymentType': 'WEB_PAYMENT',
                    'confirmed': True,
                    'paymentReferenceId': payment_reference_id,
                },
                'bookingPaidType': 'PAID_IN_FULL',
            })

        try:
            res = self.api.post('/booking.json/%s/confirm' % self.booking_id, body, {
                'sendCustomerNotification': send_customer_notification,
            })
        except BokunApiException as e:
            if e.message == 'Transaction is Inactive':
                raise self.CartException('Invalid payment id. Already used.')

            raise

        self._reservation_state = res.json()

        return self

    @property
    def totalAmount(self):
        return self._state['customerInvoice']['totalAsMoney']['amount']

    @property
    def currency(self):
        return self._state['customerInvoice']['currency']

    @property
    def booking_id(self):
        return self._reservation_state.get('bookingId')

    class CartException(Exception):
        pass
