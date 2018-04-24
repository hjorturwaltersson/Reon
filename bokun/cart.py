import uuid
from operator import itemgetter
from datetime import time, timedelta

import arrow
from inflection import dasherize

from .bokun_api import BokunApi, BokunApiException


def parse_time_str(tstr):
    return time(*[int(t) for t in tstr.split(':')])

def nearest(items, pivot):
    return min(items, key=lambda x: abs(x - pivot))

def seconds(tstr):
    return int(timedelta(*[int(t) for t in tstr.split(':')]).total_seconds())


class Cart:
    def __init__(self, api=None, session_id=None):
        self.api = BokunApi() if api is None else api

        if session_id is None:
            self.session_id = uuid.uuid4()
        else:
            self.session_id = session_id

        self._update_state()

        self._reservation_state = {}

    def _update_state(self):
        """
        Private method used to update the internal state of the Cart instance
        """
        self._state = self.api.get('/shopping-cart.json/session/%s' % self.session_id).json()

    def _apply_promo_code(self, promo_code):
        """
        Private method used by the `promo_code` property setter to apply a promo code
        """
        if self.promo_code == promo_code:
            return False

        url = '/shopping-cart.json/session/%s/apply-promo-code' % self.session_id

        res_code = self.api.get(url, {
            'promoCode': promo_code,
        }).json().get('code')

        if res_code == promo_code:
            self._update_state()
            return True

        return False

    def _remove_promo_code(self):
        """
        Private method used by the `promo_code` property deleter to remove a promo code
        """
        if self.promo_code == None:
            return False

        url = '/shopping-cart.json/session/%s/remove-promo-code' % self.session_id

        result = self.api.get(url, {
            'promoCode': self.promo_code,
        }).json().get('result')

        if result == 'success':
            self._update_state()
            return True

        return False

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

            start_time = seconds(start_time)

            avail_times = {seconds(tstr): id for tstr, id in avail_start_times.items()}

            start_time_id = avail_times[nearest(avail_times.keys(), start_time)]

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
                fields=None,
                discount_amount=0,
                discount_percentage=0):
        body = {
            'discountAmount': discount_amount,
            'discountPercentage': discount_percentage,
        }

        self._merge_booking_fields(body, fields)

        if answers is not None:
            body.update({
                'answers': {
                    'answers': [{
                        'type': dasherize(key),
                        'answer': value,
                    } for key, value in answers.items()]
                }
            })

        res = self.api.post('/booking.json/guest/%s/reserve' % self.session_id, body)

        self._reservation_state = res.json()

        return self

    def charge_card(self, card_number, cvc, exp_month, exp_year, card_holder_name, amount=None):
        body = {
            'amount': self.total_amount if amount is None else amount,
            'confirmBookingOnSuccess': False,
            'card': {
                'cardNumber': card_number,
                'cvc': cvc,
                'expMonth': exp_month,
                'expYear': exp_year,
                'name': card_holder_name,
            },
        }

        res = self.api.post('/booking.json/%s/charge-card' % self.booking_id, body, {
            'sendCustomerNotification': False,
        })

        # TODO: Check for errors

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
                    'amount': self.total_amount,
                    'currency': self.currency,
                    'paymentType': 'WEB_PAYMENT',
                    'confirmed': True,
                    'paymentReferenceId': payment_reference_id or str(uuid.uuid4()),
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
    def total_amount(self):
        try:
            return self._reservation_state['totalPrice']
        except KeyError:
            return self._state['customerInvoice']['totalDiscountedAsMoney']['amount']

    @property
    def currency(self):
        return self._state['customerInvoice']['currency']

    @property
    def promo_code(self):
        return (self._state.get('promoCode') or {}).get('code')

    @promo_code.setter
    def promo_code(self, promo_code):
        if not promo_code:
            self._remove_promo_code()
        else:
            self._apply_promo_code(promo_code)

    @promo_code.deleter
    def promo_code(self):
        self._remove_promo_code()

    @property
    def booking_id(self):
        return self._reservation_state.get('bookingId')

    class CartException(Exception):
        pass
