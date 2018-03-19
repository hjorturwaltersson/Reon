import datetime
import hashlib
import hmac
import base64
import requests
import json
import uuid

from django.conf import settings

from bokun import BokunApi

from bokun_wrapper.models import (
    Vendor,
    Place,
    Product,
    FrontPageProduct,
    CrossSaleItem,
    RequestLog,
)

bokun_api = BokunApi()
bokun_api_bl = BokunApi(
    access_key=settings.BOKUN_ACCESS_KEY_BL,
    secret_key=settings.BOKUN_SECRET_KEY_BL,
)


def get_vendor_product_ids(vendor_id):
    # reply = bokun_api.post('/activity.json/search', {"vendorId": vendor_id})
    # items_dict = reply.json()['items']
    # return [p['id'] for p in items_dict]
    return ['22257', '22442', '22246', '22443', '9882', '22141', '22112', '9883',
            '9217', '22318', '9652', '22319', '22290', '22287', '11008', '11610',
            '11611', '17989', '22936', '22937', '22942']


def get_product(product_id):
    return bokun_api.get('/activity.json/%s' % product_id).json()


def update_vendor_products(vendor_id):
    product_ids = get_vendor_product_ids(vendor_id)
    print(product_ids)
    vendor = Vendor.objects.get(bokun_id=vendor_id)
    for product in Product.objects.all():
        if product.bokun_id not in product_ids:
            print("Deleting product: {}".format(product.bokun_id))
            product.delete()
    for product_id in product_ids:
        try:
            product = Product.objects.get(bokun_id=product_id)
            print("Found existing product: {}".format(product_id))
        except Product.DoesNotExist as e:
            print("Creating new product: {}".format(product_id))
            product = Product(bokun_id=product_id)
        item_dict = get_product(product_id)
        product.title = item_dict['title']
        product.excerpt = item_dict['excerpt']
        product.price = item_dict['nextDefaultPrice']
        product.photos = item_dict['photos']
        product.vendor = vendor
        product.external_id = item_dict['externalId']
        product.bookable_extras = item_dict['bookableExtras']
        product.json = item_dict
        pricing_categories = item_dict['pricingCategories']
        if len(pricing_categories) > 0:
            product.default_price_category_id = pricing_categories[0]['id']
        if len(pricing_categories) > 1:
            product.child_price_category_id = pricing_categories[1]['id']
        for bookable_extra in item_dict['bookableExtras']:
            if bookable_extra['externalId'] == 'flightdelayguarantee' or bookable_extra[
                 'externalId'] == 'DelayGuarantee':
                product.flight_delay_id = bookable_extra['id']
                product.flight_delay_question_id = bookable_extra['questions'][0]['id']
            if bookable_extra['externalId'] == 'ChildSeat14-36kg':
                product.child_seat_child_id = bookable_extra['id']
            if bookable_extra['externalId'] == 'ChildSeat0-13kg':
                product.child_seat_infant_id = bookable_extra['id']
            if bookable_extra['externalId'] == 'ExtraBaggage':
                product.extra_baggage_id = bookable_extra['id']
            if bookable_extra['externalId'] == 'OddSizeBaggage':
                product.odd_size_id = bookable_extra['id']
        product.save()
        get_places(product_id)


def create_or_update_place(places):
    indexed_places = {str(p['id']): p for p in places}
    existing_places = list(Place.objects.filter(bokun_id__in=[p["id"] for p in places]))

    for place in existing_places:
        bokun_data = indexed_places[place.bokun_id]
        place.title = bokun_data['title']
        place.location = bokun_data['location']
        place.json = bokun_data
        place.save()
    existing_places_ids = [p.bokun_id for p in existing_places]
    missing_places = []
    for place in places:
        if str(place['id']) in existing_places_ids:
            continue
        missing_places.append(Place(bokun_id=place['id'],
                                          title=place['title'],
                                          location=place['location'],
                                          json=place))
    print("Creating {} new places".format(len(missing_places)))
    Place.objects.bulk_create(missing_places)


def get_places(product_id):
    product = Product.objects.get(bokun_id=product_id)
    reply = bokun_api.get('/activity.json/{}/pickup-places'.format(product_id))
    dropoff_places = reply.json()['dropoffPlaces']
    pickup_places = reply.json()['pickupPlaces']

    def filter_function(x):
        return 'keflavík' in x['flags'] or 'economy' in x['flags']

    filtered_dropoff_places = list(filter(filter_function, dropoff_places))
    filtered_pickup_places = list(filter(filter_function, pickup_places))

    create_or_update_place(filtered_dropoff_places)
    create_or_update_place(filtered_pickup_places)

    product.dropoff_places.set([p['id'] for p in filtered_dropoff_places], clear=True)
    product.pickup_places.set([p['id'] for p in filtered_pickup_places], clear=True)


def get_availability(product_id, date, api=bokun_api):
    reply = api.get('/activity.json/%s/availabilities' % product_id, {
        'start': date,
        'end': date,
        'includeSoldOut': True,
    })

    returnlist = [{
        'extra_prices': a['extraPrices'],
        'prices_by_category': a['pricesByCategory'],
        'prices_by_rate': a['pricesByRate'],
        'rates': a['rates'],
        'sold_out': a['soldOut'],
        'start_time': a['startTime'],
        'start_time_id': a['startTimeId'],
        'unavailable': a['unavailable'],
        'availability_count': a['availabilityCount']
    } for a in reply.json()]

    return returnlist


def get_cart(session_id=None, api=bokun_api):
    if not session_id:
        session_id = str(uuid.uuid4())

    reply = api.get('/shopping-cart.json/session/{}'.format(session_id))

    return reply.json()


def add_to_cart(activity_id, start_time_id, date, pricing_category_bookings,
                session_id=None, dropoff_place_id=None, pickup_place_id=None,
                pickup=False, custom_locations=False, api=bokun_api):

    if not session_id:
        session_id = get_cart()['sessionId']

    path = '/shopping-cart.json/session/{}/activity'.format(session_id)

    body = {
        'activityId': activity_id,
        'startTimeId': start_time_id,
        'date': date,
        'pickup': pickup,
        'pricingCategoryBookings': [{
            'pricingCategoryId': pricing_category_booking['pricing_category_id'],
            'extras': [{
                'answers': [],
                'extraId': extra['extra_id'],
                'unitCount': extra['unit_count'],
            } for extra in pricing_category_booking['extras']],
        } for pricing_category_booking in pricing_category_bookings]
    }

    if not custom_locations:
        body['pickupPlaceId'] = pickup_place_id
        body['dropoffPlaceId'] = dropoff_place_id
    else:
        with ignored(Place.DoesNotExist):
            pickup_place_id = Place.objects.get(pk=pickup_place_id).title

        body['pickupPlaceDescription'] = pickup_place_id

        with ignored(Place.DoesNotExist):
            dropoff_place_id = Place.objects.get(pk=dropoff_place_id).title or None

        body['dropoffPlaceDescription'] = dropoff_place_id

    reply = api.post(path, body)

    RequestLog.objects.create(
        outgoing_body=body,
        bokun_response=reply.json()
    )

    return reply.json()


def remove_activity_from_cart(session_id, booking_id):
    path = '/shopping-cart.json/session/{}/remove-activity/{}'.format(session_id, booking_id)
    reply = bokun_api.get(path)
    return reply.json()


def remove_extra_from_cart(session_id, booking_id, extra_id):
    path = '/shopping-cart.json/session/{}/remove-extra/ACTIVITY_BOOKING/{}/{}'.format(session_id, booking_id, extra_id)
    reply = bokun_api.get(path)
    return reply.json()


def get_crosssale_products():
    path1 = '/product-list.json/1340'
    path2 = '/product-list.json/1354'

    reply1 = bokun_api.get(path1)
    reply2 = bokun_api.get(path2)

    return [reply1.json(), reply2.json()]


def add_or_update_extra(session_id, booking_id, extra_id, unit_count):
    path = '/shopping-cart.json/session/{}/add-or-update-extra/ACTIVITY_BOOKING/{}'.format(session_id, booking_id)
    body = {
        'extraId': extra_id,
        'unitCount': unit_count
    }
    reply = bokun_api.post(path, body)
    return reply.json()


def reserve_pay_confirm(session_id, address_city, address_country, address_line_1,
                        address_line_2, address_post_code, card_number, cvc, exp_month,
                        exp_year, name, first_name, last_name, email, phone_number):
    path = '/booking.json/guest/{}/reserve-pay-confirm'.format(session_id)
    body = {
        'chargeRequest': {
            'confirmBookingOnSuccess': True,
            'card': {
                'addressCity': address_city,
                'addressCountry': address_country,
                'addressLine1': address_line_1,
                'addressLine2': address_line_2,
                'addressPostCode': address_post_code,
                'cardNumber': card_number,  # todo vista í gagnagrunn
                'cvc': cvc,
                'expMonth': exp_month,
                'expYear': exp_year,
                'name': name
            }
        },
        'answers': {
            'answers': [
                {
                    'type': 'first-name',
                    'answer': first_name
                },
                {
                    'type': 'last-name',
                    'answer': last_name
                },
                {
                    'type': 'email',
                    'answer': email
                },
                {
                    'type': 'phone-number',
                    'answer': phone_number
                }
            ]
        }
    }

    if card_number == "4111111111111111":
        reply = json.loads(open('payment.json', 'r').read())
        print(body)
        return reply

    reply = bokun_api.post(path, body)

    RequestLog.objects.create(
        bokun_response=reply.json()
    )

    return reply.json()


def sync_cross_sale_products():
    cross_sale_lists = get_crosssale_products()
    for cross_sale_list in cross_sale_lists:
        for item in cross_sale_list['items']:
            activity = item['activity']
            bokun_id = activity['id']
            try:
                product = CrossSaleItem.objects.get(bokun_id=bokun_id)
                print("Found existing product: {}".format(bokun_id))
            except CrossSaleItem.DoesNotExist as e:
                print("Creating new product: {}".format(bokun_id))
                product = CrossSaleItem(bokun_id=bokun_id)
            product.json = activity
            pricing_categories = activity['pricingCategories']
            for category in pricing_categories:
                if category['ticketCategory'] == 'ADULT':
                    product.adult_category_id = category['id']
                if category['ticketCategory'] == 'TEENAGER':
                    product.teenager_category_id = category['id']
                if category['ticketCategory'] == 'CHILD':
                    product.child_category_id = category['id']
                if category['ticketCategory'] == 'OTHER':
                    product.child_category_id = category['id']
            extras = activity['bookableExtras']
            for extra in extras:
                if "Earphones" in extra['title']:
                    product.earphone_id = extra['id']
                if "jacket" in extra['title']:
                    product.jacket_id = extra['id']
                    product.jacket_question_id = extra['questions'][0]['id']
                if "boots" in extra['title']:
                    product.boots_id = extra['id']
                    product.boots_question_id = extra['questions'][0]['id']
                if "Extra cost" in extra['title']:
                    product.extra_person_id = extra['id']
                if "Lunch" in extra['title']:
                    product.lunch_id = extra['id']
                    product.lunch_question_id = extra['questions'][0]['id']
            product.save()
