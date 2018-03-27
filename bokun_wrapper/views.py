import json
from datetime import datetime

import arrow
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, views, serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from bokun import Cart, BokunApiException
from bokun_wrapper import get_data
from .get_data import bokun_api, bokun_api_bl
from .models import (
    Vendor,
    Place,
    Product,
    FrontPageProduct,
    CrossSaleItem,
    RequestLog,
)

from .serializers import (
    ProductSerializer,
    VendorSerializer,
    PlaceSerializer,
    FrontPageProductSerializer,
)


def get_extra(extra_id, qid=None, answer=None):
    answers = []
    if qid:
        answers = [{
            'answers': [{
                'answer': answer,
                'questionId': qid
            }]
        }]

    dic = {
        'extraId': extra_id,
        'unitCount': 1,
        'answers': answers
    }
    return dic


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.all()
        pickup_place = self.request.query_params.get('pickup_place', None)
        dropoff_place = self.request.query_params.get('dropoff_place', None)
        if pickup_place:
            queryset = queryset.filter(pickup_places=pickup_place) | queryset.filter(pickup_places=None)
        if dropoff_place:
            queryset = queryset.filter(dropoff_places=dropoff_place) | queryset.filter(dropoff_places=None)
        return queryset


class PlaceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Place.objects.filter(vendor_id=942).order_by('ordering', 'title')
    serializer_class = PlaceSerializer


class VendorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer


@api_view(['GET'])
def get_availability(request):
    product_id = request.query_params['product_id']
    date = request.query_params['date']
    return Response(get_data.get_availability(product_id, date))


@api_view(['GET'])
def blue_lagoon_places(request):
    kef_places = Place.objects.filter(type='airport')

    rey_places = Place.objects.filter(vendor_id=2927)

    kef_dicts = [{
        "PickupLocation": p.title,
        "PickupLocationAddress": p.location['address'],
        "PickupBusStop": p.location['address'],
        "PickupRouteID": 1,
        "PickupLocationID": p.id,
        "RouteIDPrice": "3000"
    } for p in kef_places]

    rey_dicts = [{
        "PickupLocation": p.title,
        "PickupLocationAddress": p.location['address'],
        "PickupBusStop": p.location['address'],
        "PickupRouteID": 2,
        "PickupLocationID": p.id,
        "RouteIDPrice": "3000"
    } for p in rey_places]

    reply = {
        "KefPlaces": kef_dicts,
        "ReyPlaces": rey_dicts
    }

    return Response(reply)


class BlueLagoonOrderSerializer(serializers.Serializer):
    BookingID = serializers.CharField(required=False)
    PaymentID = serializers.CharField(required=False)

    PickupLocationID = serializers.PrimaryKeyRelatedField(
        queryset=Place.objects.filter(type__in=['airport', 'hotel']))
    DropOffLocationID = serializers.PrimaryKeyRelatedField(
        queryset=Place.objects.filter(type__in=['airport', 'hotel']))

    PickupDate = serializers.DateField()
    PickupTime = serializers.TimeField()

    PickupQuantityAdult = serializers.IntegerField(min_value=0)
    PickupQuantityChildren = serializers.IntegerField(min_value=0, default=0)

    Name = serializers.CharField()
    Email = serializers.CharField()
    PhoneNumber = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    SendConfirmationEmail = serializers.BooleanField(default=True)
    MarkPaid = serializers.BooleanField(default=True)


@api_view(['POST'])
def blue_lagoon_order_test(request):
    try:
        secret = request.META['HTTP_SECRET']
        if secret != 'WKSqWWTjmD6p2yX7Am4y8m2N':
            return Response({"success": False, "error": "authorization_failed"}, status=401)
    except Exception as e:
        return Response({"success": False, "error": "authorization_failed"}, status=401)
    try:
        body = json.loads(request.body)
        BookingID = body['BookingID']
        PickupLocationID = body['PickupLocationID']
        PickupTime = body['PickupTime']
        DropOffLocationID = body['DropOffLocationID']
        PickupQuantityAdult = body['PickupQuantityAdult']
        PickupQuantityChildren = body['PickupQuantityChildren']
        Name = body['Name']
        Email = body['Email']
        PhoneNumber = body['PhoneNumber']
        PickupDate = body['PickupDate']
        PickupDate = datetime.strptime(PickupDate, "%Y-%m-%d")
        return Response({"success": True, "error": None}, status=201)
    except Exception as e:
        return Response({"success": False, "error": "request_incomplete"}, status=400)



@csrf_exempt
@api_view(['POST'])
def blue_lagoon_order(request):
    secret = request.META.get('HTTP_SECRET')

    if secret != 'WKSqWWTjmD6p2yX7Am4y8m2N':
        return Response({
            'success': False,
            'error': 'authorization_failed'
        }, status=401)
    log = RequestLog()
    log.incoming_body = request.data
    log.url = 'blo'
    log.save()
    serializer = BlueLagoonOrderSerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'request_incomplete',
            'fields': serializer.errors,
        }, status=400)

    data = serializer.validated_data

    pickup_dt = arrow.get(datetime.combine(data['PickupDate'], data['PickupTime']))
    next_pickup_dt = pickup_dt.shift(hours=3)

    pickup_place = data['PickupLocationID']
    dropoff_place = data['DropOffLocationID']

    if pickup_place.type == 'airport':
        pickup_activity_id = 22287  # AD: Keflavík Airport to Blue Lagoon
    elif pickup_place.type == 'hotel':
        pickup_activity_id = 22277  # BLD: Transfer Reykjavík - Blue Lagoon

    if dropoff_place.type == 'airport':
        dropoff_activity_id = 22290  # AD: Blue Lagoon to Keflavík Airport
    elif dropoff_place.type == 'hotel':
        dropoff_activity_id = 22284  # BLD: Transfer Blue Lagoon - Reykjavík

    # Create new carts and get the session id:
    try:
        cart = Cart(api=bokun_api_bl)

        common_booking_data = {
            'adults': data['PickupQuantityAdult'],
            'children': data['PickupQuantityChildren'],
        }

        cart.add_activity(
            activity_id=pickup_activity_id,
            start_date=pickup_dt.format('YYYY-MM-DD'),
            start_time=pickup_dt.format('HH:mm'),
            strict_time=True,
            pickup_place_id=pickup_place.pk,
            dropoff_place_id=None,  # We know that this is the Blue Lagoon
            **common_booking_data
        )

        cart.add_activity(
            activity_id=dropoff_activity_id,
            start_date=next_pickup_dt.format('YYYY-MM-DD'),
            start_time=next_pickup_dt.format('HH:mm'),
            strict_time=False,
            pickup_place_id=None,  # We know that this is the Blue Lagoon
            dropoff_place_id=dropoff_place.pk,
            **common_booking_data
        )

        name_parts = data.get('Name', '').strip().split()

        external_booking_id = data.get('BookingID')
        external_payment_id = data.get('PaymentID')

        cart.reserve(
            fields={
                'external_booking_id': external_booking_id,
                'external_payment_id': external_payment_id,
            },
            answers={
                'first-name': ' '.join(name_parts[:1]),
                'last-name': ' '.join(name_parts[1:]),
                'email': data.get('Email', '').strip(),
                'phone-number': (data.get('PhoneNumber') or '').strip(),
            }
        )

        cart.confirm(
            mark_paid=True,
            send_customer_notification=data['SendConfirmationEmail'],
            reference_id=external_booking_id,
            payment_reference_id=external_payment_id,
        )
    except Cart.CartException as e:
        return Response({
            'success': False,
            'error': 'cart_error',
            'message': str(e)
        }, status=400)
    except BokunApiException as e:
        return Response({
            'success': False,
            'error': 'bokun_api_error',
            'message': e.message
        }, status=400)

    return Response({
        'success': True,
        'error': None,
        'bokun_reservation_data': cart._reservation_state,
    }, status=201)


def get_pricing_category_bookings(
    product,
    traveler_count_adults=0,
    traveler_count_children=0,
    flight_delay_guarantee=False,
    flight_number=None,
    extra_baggage_count=0,
    odd_size_baggage_count=0,
    child_seat_child_count=0,
    child_seat_infant_count=0
):
    category_id = product.default_price_category_id
    pricing_category_bookings = []
    for x in range(traveler_count_adults):
        pricing_category_bookings.append({
            'pricing_category_id': category_id,
            'extras': []
        })

    if product.child_price_category_id:
        category_id = product.child_price_category_id

    for x in range(traveler_count_children):
        pricing_category_bookings.append({
            'pricing_category_id': category_id,
            'extras': []
        })

    for pricing_category_booking in pricing_category_bookings:
        if flight_delay_guarantee:
            pricing_category_booking['extras'].append({
                'extra_id': product.flight_delay_id,
                'unit_count': 1,
                'answers': [{
                    'answers': [{
                        'answer': flight_number,
                        'questionId': product.flight_delay_question_id
                    }]
                }]
            })

        if extra_baggage_count > 0:
            pricing_category_booking['extras'].append({
                'extra_id': product.extra_baggage_id,
                'unit_count': extra_baggage_count
            })
            extra_baggage_count = 0

        if odd_size_baggage_count > 0:
            pricing_category_booking['extras'].append({
                'extra_id': product.odd_size_id,
                'unit_count': odd_size_baggage_count
            })
            odd_size_baggage_count = 0

        if child_seat_child_count > 0:
            pricing_category_booking['extras'].append({
                'extra_id': product.child_seat_child_id,
                'unit_count': child_seat_child_count
            })
            child_seat_child_count = 0

        if child_seat_infant_count > 0:
            pricing_category_booking['extras'].append({
                'extra_id': product.child_seat_infant_id,
                'unit_count': child_seat_child_count
            })
            child_seat_infant_count = 0

    return pricing_category_bookings


@api_view(['POST'])
def add_to_cart(request):
    body = json.loads(request.body)
    session_id = body.get('session_id')

    product_type_id = body['product_type_id']

    date = body['date']
    return_date = body.get('return_date')

    pickup_place_id = body.get('pickup_place_id')
    dropoff_place_id = body.get('dropoff_place_id')

    traveler_count_adults = int(body.get('traveler_count_adults', 0))
    traveler_count_children = int(body.get('traveler_count_children', 0))

    flight_delay_guarantee = body.get('flight_delay_guarantee', False)
    flight_number = body.get('flight_number', "")
    flight_number_return = body.get('flight_number_return', '')

    extra_baggage_count = int(body.get('extra_baggage_count', 0))
    odd_size_baggage_count = int(body.get('odd_size_baggage_count', 0))

    child_seat_child_count = int(body.get('child_seat_child_count', 0))
    child_seat_infant_count = int(body.get('child_seat_infant_count', 0))

    return_pickup_place_id = body.get('return_pickup_place_id', dropoff_place_id)
    return_dropoff_place_id = body.get('return_dropoff_place_id', pickup_place_id)

    is_round_trip = (return_date is not None)

    hotel_connection = body.get('hotel_connection', False)

    if hotel_connection:
        if product_type_id == 11:
            product_type_id = 19

        if product_type_id == 12:
            product_type_id = 18

    product = FrontPageProduct.objects.get(id=product_type_id)
    custom_locations = False

    if product.luxury or product.private:
        main_product = product.bokun_product
        return_product = product.bokun_product
        traveler_count_children = 0
        traveler_count_adults = 1
        custom_locations = True
    elif is_round_trip and product.discount_product:
        main_product = product.discount_product
        return_product = product.return_product
    else:
        main_product = product.bokun_product
        return_product = product.return_product

    pricing_category_bookings = get_pricing_category_bookings(
        main_product,
        traveler_count_adults,
        traveler_count_children,
        flight_delay_guarantee,
        flight_number,
        extra_baggage_count,
        odd_size_baggage_count,
        child_seat_child_count,
        child_seat_infant_count,
    )

    start_dt = arrow.get(date)

    reply1 = get_data.add_to_cart(
        activity_id=main_product.id,
        start_time_id=main_product.get_start_time_id(start_dt),
        date=start_dt.format('YYYY-MM-DD'),
        pricing_category_bookings=pricing_category_bookings,
        session_id=session_id,
        dropoff_place_id=dropoff_place_id,
        pickup_place_id=pickup_place_id,
        custom_locations=custom_locations,
    )

    RequestLog.objects.create(
        url=request.get_full_path(),
        incoming_body=body,
        bokun_response=reply1
    )

    try:
        session_id = reply1['sessionId']
    except KeyError:
        return Response(reply1)

    if is_round_trip:
        pricing_category_bookings = get_pricing_category_bookings(
            return_product,
            traveler_count_adults,
            traveler_count_children,
            flight_delay_guarantee,
            flight_number_return,
            extra_baggage_count,
            odd_size_baggage_count,
            child_seat_child_count,
            child_seat_infant_count,
        )

        return_start_dt = arrow.get(return_date)

        reply2 = get_data.add_to_cart(
            activity_id=return_product.id,
            start_time_id=return_product.get_start_time_id(return_start_dt),
            date=return_start_dt.format('YYYY-MM-DD'),
            pricing_category_bookings=pricing_category_bookings,
            session_id=session_id,
            dropoff_place_id=return_dropoff_place_id,
            pickup_place_id=return_pickup_place_id,
            custom_locations=custom_locations,
        )

        RequestLog.objects.create(
            url=request.get_full_path(),
            incoming_body=body,
            bokun_response=reply2,
        )

        return Response(reply2)

    return Response(reply1)


@api_view(['POST'])
def add_extra_to_cart(request):
    body = json.loads(request.body)
    session_id = body['session_id']
    booking_id = body['booking_id']
    extra_id = body['extra_id']
    unit_count = body['unit_count']
    return Response(get_data.add_or_update_extra(session_id, booking_id, extra_id, unit_count))


@api_view(['GET'])
def get_cart(request):
    session_id = request.query_params.get('session_id', None)
    return Response(get_data.get_cart(session_id))


@api_view(['POST'])
def pay(request):
    body = json.loads(request.body)
    session_id = body['session_id']
    address_city = body['address_city']
    address_country = body['address_country']
    address_line_1 = body['address_line_1']
    address_line_2 = body['address_line_2']
    address_post_code = body['address_post_code']
    card_number = body['card_number']
    cvc = body['cvc']
    exp_month = body['exp_month']
    exp_year = body['exp_year']
    name = body['name']
    first_name = body.get('first_name')
    last_name = body.get('last_name')
    email = body.get('email')
    phone_number = body.get('phone_number', '')
    return Response(get_data.reserve_pay_confirm(session_id=session_id,
                                                 address_city=address_city,
                                                 address_country=address_country,
                                                 address_line_1=address_line_1,
                                                 address_line_2=address_line_2,
                                                 address_post_code=address_post_code,
                                                 card_number=card_number,
                                                 cvc=cvc,
                                                 exp_month=exp_month,
                                                 exp_year=exp_year,
                                                 name=name,
                                                 first_name=first_name,
                                                 last_name=last_name,
                                                 email=email,
                                                 phone_number=phone_number))


@api_view(['POST'])
def remove_extra_from_cart(request):
    body = json.loads(request.body)
    session_id = body['session_id']
    booking_id = body['booking_id']
    extra_id = body['extra_id']
    return Response(get_data.remove_extra_from_cart(session_id, booking_id, extra_id))


@api_view(['POST'])
def remove_activity_from_cart(request):
    body = json.loads(request.body)
    session_id = body['session_id']
    booking_id = body['booking_id']
    return Response(get_data.remove_activity_from_cart(session_id, booking_id))


@api_view(['GET'])
def get_cross_sale(request):
    return Response(get_data.get_crosssale_products())


@api_view(['POST'])
def add_cross_sale_to_cart(request):
    body = json.loads(request.body)

    session_id = body.get('session_id')
    activity_id = body.get('activity_id')

    date = body.get('date', '')

    start_time_id = body.get('start_time_id')

    adult_count = body.get('adult_count', 0)
    teenager_count = body.get('teenager_count', 0)
    child_count = body.get('child_count', 0)

    pickup_location_id = body.get('pickup_location_id')

    cross_sale_item = CrossSaleItem.objects.get(id=activity_id)

    bokun_body = {
        'activityId': activity_id,
        'date': date,
        'pickup': pickup_location_id is not None,
        'pickupPlaceId': pickup_location_id,
        'startTimeId': start_time_id,
        'pricingCategoryBookings': [{
            'pricingCategoryId': cross_sale_item.default_price_category_id,
            'extras': [],
        } for x in range(adult_count)] + [{
            'pricingCategoryId': cross_sale_item.teenager_price_category_id,
            'extras': [],
        } for x in range(teenager_count)] + [{
            'pricingCategoryId': cross_sale_item.child_price_category_id,
            'extras': [],
        } for x in range(child_count)]
    }

    from pprint import pprint
    pprint(bokun_body)

    path = '/shopping-cart.json/session/%s/activity' % session_id

    reply = get_data.bokun_api.post(path, bokun_body)

    RequestLog.objects.create(
        url=request.get_full_path(),
        incoming_body=body,
        outgoing_body=bokun_body,
        bokun_response=reply.json()
    )

    try:
        return Response(reply.json())
    except ValueError as e:
        return Response(reply.text)
