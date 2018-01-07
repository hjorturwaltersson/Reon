import datetime
import hashlib
import hmac
import base64
import requests
import json
from django.apps import apps
import uuid

baseurl = "https://api.bokun.is"
access_key = "7450b62343c64e12ac97f4504eb4386f"
secret_key = "b958b750cd51462580c2a1c0ac7110c6"


def make_get_request(path):
    url = baseurl + path
    now_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    method = "GET"
    token = "{}{}{}{}".format(now_date, access_key, method, path)
    digester = hmac.new(bytes(secret_key, "ascii"), bytes(token, "ascii"), hashlib.sha1)
    signature = base64.standard_b64encode(digester.digest())
    headers = {
        "X-Bokun-Date": now_date,
        "X-Bokun-AccessKey": access_key,
        "X-Bokun-Signature": signature.decode("ascii")
    }
    reply = requests.get(url, headers=headers)
    return reply


def make_post_request(path, body):
    url = baseurl + path
    now_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    method = "POST"
    token = "{}{}{}{}".format(now_date, access_key, method, path)
    digester = hmac.new(bytes(secret_key, "ascii"), bytes(token, "ascii"), hashlib.sha1)
    signature = base64.standard_b64encode(digester.digest())
    headers = {
        "X-Bokun-Date": now_date,
        "X-Bokun-AccessKey": access_key,
        "X-Bokun-Signature": signature.decode("ascii"),
        "Content-Type": "application/json"
    }
    reply = requests.post(url, headers=headers, data=json.dumps(body))
    return reply


def get_vendor_product_ids(vendor_id):
    reply = make_post_request('/activity.json/search', {"vendorId": vendor_id})
    items_dict = reply.json()['items']
    ids = [p['id'] for p in items_dict]
    return ids


def get_product(product_id):
    reply = make_get_request('/activity.json/{}'.format(product_id))
    return reply.json()


def update_vendor_products(vendor_id):
    product_ids = get_vendor_product_ids(vendor_id)
    vendor_model = apps.get_model('bokun_wrapper', 'Vendor')
    product_model = apps.get_model('bokun_wrapper', 'Product')
    vendor = vendor_model.objects.get(bokun_id=vendor_id)
    for product in product_model.objects.all():
        if product.bokun_id not in product_ids:
            product.delete()
    for product_id in product_ids:
        try:
            product = product_model.objects.get(bokun_id=product_id)
        except product_model.DoesNotExist as e:
            product = product_model(bokun_id=product_id)
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
            product.teenager_price_category_id = pricing_categories[1]['id']
        if len(pricing_categories) > 2:
            product.child_price_category_id = pricing_categories[2]['id']
        for bookable_extra in item_dict['bookableExtras']:
            if bookable_extra['external_id'] is 'flightdelayguarantee':
                product.flight_delay_id = bookable_extra['id']
                product.flight_delay_question_id = bookable_extra['questions'][0]['id']
            if bookable_extra['external_id'] is 'ChildSeat14-36kg':
                product.child_seat_child_id = bookable_extra['id']
            if bookable_extra['external_id'] is 'ChildSeat0-13kg':
                product.child_seat_infant_id = bookable_extra['id']
            if bookable_extra['external_id'] is 'ExtraBaggage':
                product.extra_baggage_id = bookable_extra['id']
            if bookable_extra['external_id'] is 'OddSizeBaggage':
                product.odd_size_id = bookable_extra['id']
        product.save()
        get_places(product_id)


def create_or_update_place(places):
    place_model = apps.get_model('bokun_wrapper', 'Place')
    indexed_places = {str(p['id']): p for p in places}
    existing_places = list(place_model.objects.filter(bokun_id__in=[p["id"] for p in places]))

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
        missing_places.append(place_model(bokun_id=place['id'],
                                          title=place['title'],
                                          location=place['location'],
                                          json=place))
    place_model.objects.bulk_create(missing_places)


def get_places(product_id):
    product_model = apps.get_model('bokun_wrapper', 'Product')
    product = product_model.objects.get(bokun_id=product_id)
    reply = make_get_request('/activity.json/{}/pickup-places'.format(product_id))
    dropoff_places = reply.json()['dropoffPlaces']
    pickup_places = reply.json()['pickupPlaces']

    create_or_update_place(dropoff_places)
    create_or_update_place(pickup_places)

    product.dropoff_places.set([p['id'] for p in dropoff_places], clear=True)
    product.pickup_places.set([p['id'] for p in pickup_places], clear=True)


def get_availability(product_id, date):
    reply = make_get_request('/activity.json/{}/availabilities?start={}&end={}&includeSoldOut=true'.format(product_id, date, date))
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


def get_cart(session_id=None):
    if not session_id:
        session_id = str(uuid.uuid4())
    reply = make_get_request('/shopping-cart.json/session/{}'.format(session_id))
    return reply.json()


def add_to_cart(activity_id, start_time_id, date, pricing_category_bookings,
                session_id=None, dropoff_place_id=None, pickup_place_id=None):
    if not session_id:
        session_id = get_cart()['sessionId']
    path = '/shopping-cart.json/session/{}/activity'.format(session_id)
    body = {
        'activityId': activity_id,
        'startTimeId': start_time_id,
        'date': date,
        'pickup': False
    }
    pricing_category_bookings_list = []
    for pricing_category_booking in pricing_category_bookings:
        extra_list = []
        for extra in pricing_category_booking['extras']:
            extra_list.append({
                "answers": [],
                "extraId": extra['extra_id'],
                "unitCount": extra['unit_count']
            })
        pricing_category_bookings_list.append({
            "extras": extra_list,
            "pricingCategoryId": pricing_category_booking['pricing_category_id']
        })
    body['pricingCategoryBookings'] = pricing_category_bookings_list
    if dropoff_place_id:
        body['dropoffPlaceId'] = dropoff_place_id
    if pickup_place_id:
        body['pickupPlaceId'] = pickup_place_id
    reply = make_post_request(path, body)
    return reply.json()


def remove_activity_from_cart(session_id, booking_id):
    path = '/shopping-cart.json/session/{}/remove-activity/{}'.format(session_id, booking_id)
    reply = make_get_request(path)
    return reply.json()


def remove_extra_from_cart(session_id, booking_id, extra_id):
    path = '/shopping-cart.json/session/{}/remove-extra/ACTIVITY_BOOKING/{}/{}'.format(session_id, booking_id, extra_id)
    reply = make_get_request(path)
    return reply.json()


def add_or_update_extra(session_id, booking_id, extra_id, unit_count):
    path = '/shopping-cart.json/session/{}/add-or-update-extra/ACTIVITY_BOOKING/{}'.format(session_id, booking_id)
    body = {
        'extraId': extra_id,
        'unitCount': unit_count
    }
    reply = make_post_request(path, body)
    return reply.json()


def reserve_pay_confirm(session_id, address_city, address_country, address_line_1,
                        address_line_2, address_post_code, card_number, cvc, exp_month,
                        exp_year, name):
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
        }
    }
    reply = make_post_request(path, body)
    return reply.json()


def get_payment(session_id):
    path = '/booking.json/guest/{}/reserve-pay-confirm'.format(session_id)
    now_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    method = "POST"
    token = "{}{}{}{}".format(now_date, access_key, method, path)
    digester = hmac.new(bytes(secret_key, "ascii"), bytes(token, "ascii"), hashlib.sha1)
    signature = base64.standard_b64encode(digester.digest())
    headers = {
        "X-Bokun-Date": now_date,
        "X-Bokun-AccessKey": access_key,
        "X-Bokun-Signature": signature.decode("ascii"),
        "Content-Type": "application/json"
    }
    return {
        "path": path,
        "headers": headers
    }
