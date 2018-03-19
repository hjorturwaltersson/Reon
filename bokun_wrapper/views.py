import json
from datetime import datetime

import arrow
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, views, serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from bokun import Cart
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
    queryset = Place.objects.all().order_by('ordering', 'title')
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

    rey_places = Place.objects.filter(type='hotel')

    kef_dicts = [{
        "PickupLocation": p.title,
        "PickupLocationAddress": "Laugarvegur 104",
        "PickupRouteID": 1,
        "PickupLocationID": p.bokun_id,
        "RouteIDPrice": "3000"
    } for p in kef_places]

    rey_dicts = [{
        "PickupLocation": p.title,
        "PickupLocationAddress": "Laugarvegur 104",
        "PickupRouteID": 2,
        "PickupLocationID": p.bokun_id,
        "RouteIDPrice": "3000"
    } for p in rey_places]

    reply = {
        "KefPlaces": kef_dicts,
        "ReyPlaces": rey_dicts
    }

    return Response(reply)


class BlueLagoonOrderSerializer(serializers.Serializer):
    ROUTE_CHOICES = (
        ('KEF-BLD-KEF', 'KEF-BLD-KEF'),
        ('KEF-BLD-RVK', 'KEF-BLD-RVK'),
        ('RVK-BLD-RVK', 'RVK-BLD-RVK'),
        ('RVK-BLD-KEF', 'RVK-BLD-KEF'),
    )

    Route = serializers.ChoiceField(choices=ROUTE_CHOICES)

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
    PhoneNumber = serializers.CharField(required=False)

    SendConfirmationEmail = serializers.BooleanField(default=False)
    MarkPaid = serializers.BooleanField(default=True)



@csrf_exempt
@api_view(['POST'])
def blue_lagoon_order(request):
    secret = request.META.get('HTTP_SECRET')

    if secret != 'WKSqWWTjmD6p2yX7Am4y8m2N':
        return Response({
            'success': False,
            'error': 'authorization_failed'
        }, status=401)

    serializer = BlueLagoonOrderSerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'request_incomplete',
            'fields': serializer.errors,
        }, status=400)

    data = serializer.validated_data

    pickup_dt = arrow.get(datetime.combine(data['PickupDate'], data['PickupTime']))
    next_pickup_dt = pickup_dt.shift(hours=1)

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
            'first-name': ''.join(name_parts[:1]),
            'last-name': ''.join(name_parts[1:]),
            'email': data.get('Email', '').strip(),
            'phone-number': data.get('PhoneNumber', '').strip(),
        }
    )

    cart.confirm(
        mark_paid=True,
        send_customer_notification=data['SendConfirmationEmail'],
        reference_id=external_booking_id,
        payment_reference_id=external_payment_id,
    )

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
    product_type_id = body['product_type_id']
    start_time_id = body['start_time_id']
    date = body['date']
    pickup_place_id = body['pickup_place_id']
    dropoff_place_id = body['dropoff_place_id']
    round_trip = body['round_trip']
    traveler_count_adults = body.get('traveler_count_adults', 0)
    traveler_count_children = body.get('traveler_count_children', 0)
    session_id = body.get('session_id', None)
    return_start_time_id = body.get('return_start_time_id', None)
    return_date = body.get('return_date', None)
    flight_delay_guarantee = body.get('flight_delay_guarantee', False)
    flight_number = body.get('flight_number', "")
    flight_number_return = body.get('flight_number_return', '')
    extra_baggage_count = body.get('extra_baggage_count', 0)
    odd_size_baggage_count = body.get('odd_size_baggage_count', 0)
    child_seat_child_count = body.get('child_seat_child_count', 0)
    child_seat_infant_count = body.get('child_seat_infant_count', 0)
    return_pickup_place_id = body.get('return_pickup_place_id', dropoff_place_id)
    return_dropoff_place_id = body.get('return_dropoff_place_id', pickup_place_id)

    hotel_connection = body.get('hotel_connection', False)
    if hotel_connection and product_type_id == 11:
        product_type_id = 19
        if round_trip:
            start_time = get_start_time(start_time_id, 9883, date)
            start_time_id = get_start_time_id(22443, date, start_time)
            return_start_time = get_start_time(return_start_time_id, 9882, return_date)
            return_start_time_id = get_start_time_id(22442, return_date, return_start_time)
        else:
            start_time = get_start_time(start_time_id, 22112, date)
            start_time_id = get_start_time_id(22246, date, start_time)

    if hotel_connection and product_type_id == 12:
        product_type_id = 18
        if round_trip:
            start_time = get_start_time(start_time_id, 9882, date)
            start_time_id = get_start_time_id(22442, date, start_time)
            return_start_time = get_start_time(return_start_time_id, 9883, return_date)
            return_start_time_id = get_start_time_id(22443, return_date, return_start_time)
        else:
            start_time = get_start_time(start_time_id, 22141, date)
            start_time_id = get_start_time_id(22257, date, start_time)

    traveler_count_adults = int(traveler_count_adults)
    traveler_count_children = int(traveler_count_children)
    extra_baggage_count = int(extra_baggage_count)
    odd_size_baggage_count = int(odd_size_baggage_count)
    child_seat_child_count = int(child_seat_child_count)
    child_seat_infant_count = int(child_seat_infant_count)
    product = FrontPageProduct.objects.get(id=product_type_id)
    custom_locations = False

    if product.luxury or product.private:
        main_product = product.bokun_product
        return_product = product.bokun_product
        traveler_count_children = 0
        traveler_count_adults = 1
        custom_locations = True
    elif round_trip and product.discount_product:
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
        child_seat_infant_count)

    reply1 = get_data.add_to_cart(activity_id=main_product.bokun_id,
                                  start_time_id=start_time_id,
                                  date=date,
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
    except KeyError as e:
        return Response(reply1)
    if round_trip:
        pricing_category_bookings = get_pricing_category_bookings(
            return_product,
            traveler_count_adults,
            traveler_count_children,
            flight_delay_guarantee,
            flight_number_return,
            extra_baggage_count,
            odd_size_baggage_count,
            child_seat_child_count,
            child_seat_infant_count)
        reply2 = get_data.add_to_cart(activity_id=return_product.bokun_id,
                                      start_time_id=return_start_time_id,
                                      date=return_date,
                                      pricing_category_bookings=pricing_category_bookings,
                                      session_id=session_id,
                                      dropoff_place_id=return_dropoff_place_id,
                                      pickup_place_id=return_pickup_place_id,
                                      custom_locations=custom_locations,
                                      )
        RequestLog.objects.create(
            url=request.get_full_path(),
            incoming_body=body,
            bokun_response=reply2
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


def get_product_price(availability, product, traveler_count_adults, traveler_count_children):
    try:
        prices_by_category = availability[0]['prices_by_category']
        s = list(prices_by_category.values())
        adult_price = s[s.index(max(s))]
        child_price = s[s.index(min(s))]
    except Exception as e:
        return 0
    price = traveler_count_adults * adult_price + traveler_count_children * child_price
    try:
        if product.private or product.luxury:
            price = product.adult_price
    except Exception as e:
        pass
    return price


@api_view(['GET'])
def get_frontpage_products(request):
    traveler_count_adults = request.query_params.get('traveler_count_adults', 0) or 0
    traveler_count_adults = int(traveler_count_adults)
    traveler_count_children = request.query_params.get('traveler_count_children', 0) or 0
    traveler_count_children = int(traveler_count_children)
    location_from = request.query_params.get('location_from', None)
    location_to = request.query_params.get('location_to', None)
    date_from = request.query_params.get('date_from', None)
    date_to = request.query_params.get('date_to', None)
    round_trip = False
    custom_locations = False
    price = 0
    if date_to:
        round_trip = True

    total_traveler_count = traveler_count_adults + traveler_count_children

    try:
        Place.objects.get(bokun_id=location_from)
        Place.objects.get(bokun_id=location_to)
    except Place.DoesNotExist as e:
        custom_locations = True

    queryset = Product.objects.all()
    if not custom_locations:
        if location_from:
            queryset = queryset.filter(pickup_places=location_from) | queryset.filter(pickup_places=None)
        if location_to:
            queryset = queryset.filter(dropoff_places=location_to) | queryset.filter(dropoff_places=None)
    else:
        queryset = Product.objects.none()
    private_products = FrontPageProduct.objects.filter(private=True) | FrontPageProduct.objects.filter(luxury=True)
    applicable_private_products = private_products.filter(min_people__lte=total_traveler_count, max_people__gte=total_traveler_count)
    products = FrontPageProduct.objects.filter(bokun_product__in=queryset, private=False, luxury=False) | applicable_private_products
    # products = FrontPageProduct.objects.filter(private=False, luxury=False) | applicable_private_products
    reply = []
    print(products)

    for product in products:
        single_product_dict = FrontPageProductSerializer(product).data

        if round_trip and product.discount_product:
            main_product = product.discount_product
            single_product_dict['bokun_product'] = ProductSerializer(product.discount_product).data
        else:
            main_product = product.bokun_product

        availability = None
        if date_from:
            availability = get_data.get_availability(main_product.bokun_id, date_from)
            single_product_dict['availability'] = availability
        else:
            single_product_dict['availability'] = None
        single_product_dict['available'] = False
        if availability:
            price = get_product_price(availability, product, traveler_count_adults, traveler_count_children)
            single_product_dict['total_price'] = price

            for time_slot in availability:
                if time_slot['availability_count'] >= total_traveler_count or product.private or product.luxury:
                    single_product_dict['available'] = True
                    break
        return_availability = None
        if date_to:
            return_availability = get_data.get_availability(product.return_product.bokun_id, date_to)
            if not return_availability:
                continue
            single_product_dict['availability_return'] = return_availability
        else:
            single_product_dict['availability_return'] = None
        single_product_dict['available_return'] = False
        if return_availability:
            return_price = get_product_price(availability, product, traveler_count_adults, traveler_count_children)
            single_product_dict['return_price'] = return_price
            single_product_dict['total_price'] = price + return_price
            for time_slot in return_availability:
                if time_slot['availability_count'] >= total_traveler_count or product.private or product.luxury:
                    single_product_dict['available_return'] = True
                    break
        reply.append(single_product_dict)

    return Response(reply)


@api_view(['GET'])
def get_single_frontpage_product(request, **kwargs):
    traveler_count_adults = request.query_params.get('traveler_count_adults', 0) or 0
    traveler_count_adults = int(traveler_count_adults)
    traveler_count_children = request.query_params.get('traveler_count_children', 0) or 0
    traveler_count_children = int(traveler_count_children)
    total_traveler_count = traveler_count_children + traveler_count_adults
    date_from = request.query_params.get('date_from', None)
    date_to = request.query_params.get('date_to', None)
    round_trip = False
    if date_to:
        round_trip = True
    product = FrontPageProduct.objects.get(id=kwargs['id'])
    data = FrontPageProductSerializer(product).data
    if round_trip and product.discount_product:
        main_product = product.discount_product
        data['bokun_product'] = ProductSerializer(product.discount_product).data
    else:
        main_product = product.bokun_product
    if date_from:
        availability = get_data.get_availability(main_product.bokun_id, date_from)
        data['total_price'] = get_product_price(availability, product, traveler_count_adults, traveler_count_children)

        data['availability'] = []
        for time_slot in availability:
            if time_slot['availability_count'] >= total_traveler_count or product.private or product.luxury:
                data['availability'].append(time_slot)
    else:
        data['availability'] = None
    if date_to:
        return_availability = get_data.get_availability(product.return_product.bokun_id, date_to)
        data['return_price'] = get_product_price(return_availability, product.return_product, traveler_count_adults, traveler_count_children)

        data['availability_return'] = []
        for time_slot in return_availability:
            if time_slot['availability_count'] >= total_traveler_count or product.private or product.luxury:
                data['availability_return'].append(time_slot)
    else:
        data['availability_return'] = None
    data['total_price'] = data.get('total_price', 0) + data.get('return_price', 0)
    return Response(data)


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
    session_id = body.get('session_id', None)
    activity_id = body.get('activity_id', 0)
    date = body.get('date', '')
    start_time_id = body.get('start_time_id', 0)
    adult_count = body.get('adult_count', 0)
    teenager_count = body.get('teenager_count', 0)
    child_count = body.get('child_count', 0)
    earphone_count = body.get('earphone_count', 0)
    jacket_count_xsmall = body.get('jacket_count_xsmall', 0)
    jacket_count_small = body.get('jacket_count_small', 0)
    jacket_count_medium = body.get('jacket_count_medium', 0)
    jacket_count_large = body.get('jacket_count_large', 0)
    jacket_count_xlarge = body.get('jacket_count_xlarge', 0)
    shoe_count_37 = body.get('shoe_count_37', 0)
    shoe_count_38 = body.get('shoe_count_38', 0)
    shoe_count_39 = body.get('shoe_count_39', 0)
    shoe_count_40 = body.get('shoe_count_40', 0)
    shoe_count_41 = body.get('shoe_count_41', 0)
    shoe_count_42 = body.get('shoe_count_42', 0)
    shoe_count_43 = body.get('shoe_count_43', 0)
    shoe_count_44 = body.get('shoe_count_44', 0)
    lunch_count_regular = body.get('lunch_count_regular', 0)
    lunch_count_vegan = body.get('lunch_count_vegan', 0)
    lunch_count_vegetarian = body.get('lunch_count_vegetarian', 0)
    extra_person_count = body.get('extra_person_count', 0)
    pickup_location_id = body.get('pickup_location_id', 0)
    pickup = True
    if pickup_location_id == 0:
        pickup = False
    total_jackets = jacket_count_xsmall + jacket_count_small + jacket_count_medium + jacket_count_large + jacket_count_xlarge
    total_shoes = shoe_count_37 + shoe_count_38 + shoe_count_39 + shoe_count_40 + shoe_count_41 + shoe_count_42 + shoe_count_43 + shoe_count_44
    total_lunches = lunch_count_regular + lunch_count_vegan + lunch_count_vegetarian
    cross_sale_item = CrossSaleItem.objects.get(bokun_id=activity_id)

    bokun_body = {
        'activityId': activity_id,
        'date': date,
        'pickup': pickup,
        'pickupPlaceId': pickup_location_id,
        'startTimeId': start_time_id
    }
    pricing_category_bookings = []
    for x in range(adult_count):
        pricing_category_bookings.append({
            'pricingCategoryId': cross_sale_item.adult_category_id,
            'extras': []
        })
    for x in range(teenager_count):
        pricing_category_bookings.append({
            'pricingCategoryId': cross_sale_item.teenager_category_id,
            'extras': []
        })
    for x in range(child_count):
        pricing_category_bookings.append({
            'pricingCategoryId': cross_sale_item.child_category_id,
            'extras': []
        })

    # Add earphones
    for x in range(earphone_count):
        pricing_category_bookings[x]['extras'].append(get_extra(cross_sale_item.earphone_id))
    # Add extra people
    for x in range(extra_person_count):
        pricing_category_bookings[x]['extras'].append(get_extra(cross_sale_item.extra_person_id))

    # Add jackets
    for x in range(total_jackets):
        for y in range(jacket_count_xsmall):
            pricing_category_bookings[x]['extras'].append(
                get_extra(cross_sale_item.jacket_id, cross_sale_item.jacket_question_id, "X-Small")
            )
        for y in range(jacket_count_small):
            pricing_category_bookings[x]['extras'].append(
                get_extra(cross_sale_item.jacket_id, cross_sale_item.jacket_question_id, "Small")
            )
        for y in range(jacket_count_medium):
            pricing_category_bookings[x]['extras'].append(
                get_extra(cross_sale_item.jacket_id, cross_sale_item.jacket_question_id, "Medium")
            )
        for y in range(jacket_count_large):
            pricing_category_bookings[x]['extras'].append(
                get_extra(cross_sale_item.jacket_id, cross_sale_item.jacket_question_id, "Large")
            )
        for y in range(jacket_count_xlarge):
            pricing_category_bookings[x]['extras'].append(
                get_extra(cross_sale_item.jacket_id, cross_sale_item.jacket_question_id, "X-Large")
            )

    # Add shoes
    for x in range(total_shoes):
        for y in range(shoe_count_37):
            pricing_category_bookings[x]['extras'].append(
                get_extra(cross_sale_item.boots_id, cross_sale_item.boots_question_id, "EU 37")
            )
        for y in range(shoe_count_38):
            pricing_category_bookings[x]['extras'].append(
                get_extra(cross_sale_item.boots_id, cross_sale_item.boots_question_id, "EU 38")
            )
        for y in range(shoe_count_39):
            pricing_category_bookings[x]['extras'].append(
                get_extra(cross_sale_item.boots_id, cross_sale_item.boots_question_id, "EU 39")
            )
        for y in range(shoe_count_40):
            pricing_category_bookings[x]['extras'].append(
                get_extra(cross_sale_item.boots_id, cross_sale_item.boots_question_id, "EU 40")
            )
        for y in range(shoe_count_41):
            pricing_category_bookings[x]['extras'].append(
                get_extra(cross_sale_item.boots_id, cross_sale_item.boots_question_id, "EU 41")
            )
        for y in range(shoe_count_42):
            pricing_category_bookings[x]['extras'].append(
                get_extra(cross_sale_item.boots_id, cross_sale_item.boots_question_id, "EU 42")
            )
        for y in range(shoe_count_43):
            pricing_category_bookings[x]['extras'].append(
                get_extra(cross_sale_item.boots_id, cross_sale_item.boots_question_id, "EU 43")
            )
        for y in range(shoe_count_44):
            pricing_category_bookings[x]['extras'].append(
                get_extra(cross_sale_item.boots_id, cross_sale_item.boots_question_id, "EU 44")
            )

        # Add lunches
    for x in range(total_lunches):
        for y in range(lunch_count_regular):
            pricing_category_bookings[x]['extras'].append(
                get_extra(cross_sale_item.lunch_id, cross_sale_item.lunch_question_id, "Regular")
            )
        for y in range(lunch_count_vegetarian):
            pricing_category_bookings[x]['extras'].append(
                get_extra(cross_sale_item.lunch_id, cross_sale_item.lunch_question_id, "Vegetarian")
            )
        for y in range(lunch_count_vegan):
            pricing_category_bookings[x]['extras'].append(
                get_extra(cross_sale_item.lunch_id, cross_sale_item.lunch_question_id, "Vegan")
            )

    bokun_body['pricingCategoryBookings'] = pricing_category_bookings

    path = '/shopping-cart.json/session/{}/activity'.format(session_id)

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


def get_start_time_id(activity_id, date, start_time, api=bokun_api):
    data = get_data.get_availability(activity_id, date, api=api)
    for start_time_slot in data:
        if start_time_slot['start_time'] == start_time:
            return start_time_slot['start_time_id']
    return None


def get_start_time(start_time_id, activity_id, date):
    data = get_data.get_availability(activity_id, date)
    for start_time_slot in data:
        if start_time_slot['start_time_id'] == start_time_id:
            return start_time_slot['start_time']
    return ""
