from bokun_wrapper import get_data
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Vendor, Place, Product, FrontPageProduct
from .serializers import ProductSerializer, VendorSerializer, PlaceSerializer, FrontPageProductSerializer
import json


def get_private_price(count):
    if count < 5:
        return 19990
    elif count < 15:
        return 34990


def get_luxury_price(count):
    if count < 4:
        return 27990
    elif count < 8:
        return 34990


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


def get_pricing_category_bookings(product, traveler_count_adults,
                                  traveler_count_children,
                                  flight_delay_guarantee, flight_number,
                                  extra_baggage_count, odd_size_baggage_count,
                                  child_seat_child_count, child_seat_infant_count):
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

    traveler_count_adults = int(traveler_count_adults)
    traveler_count_children = int(traveler_count_children)
    total_traveler_count = traveler_count_children + traveler_count_adults
    extra_baggage_count = int(extra_baggage_count)
    odd_size_baggage_count = int(odd_size_baggage_count)
    child_seat_child_count = int(child_seat_child_count)
    child_seat_infant_count = int(child_seat_infant_count)
    product = FrontPageProduct.objects.get(id=product_type_id)
    if product.luxury:
        if total_traveler_count < 4:
            main_product = Product.objects.get(bokun_id=13282)
        else:
            main_product = Product.objects.get(bokun_id=13289)
        return_product = main_product
        traveler_count_children = 0
        traveler_count_adults = 1
    elif product.private:
        if total_traveler_count < 5:
            main_product = Product.objects.get(bokun_id=11008)
        elif total_traveler_count < 9:
            main_product = Product.objects.get(bokun_id=11610)
        else:
            main_product = Product.objects.get(bokun_id=11611)
        return_product = main_product
        traveler_count_children = 0
        traveler_count_adults = 1
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
                                      dropoff_place_id=pickup_place_id,
                                      pickup_place_id=dropoff_place_id,
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


def get_product_price(product, traveler_count_adults, traveler_count_children, round_trip):
    price = traveler_count_adults * product.adult_price + traveler_count_children * product.child_price
    if round_trip:
        price = traveler_count_adults * product.adult_price_round_trip + traveler_count_children * product.child_price_round_trip
    total_traveler_count = traveler_count_adults + traveler_count_children
    if product.private:
        price = get_private_price(total_traveler_count)
        if round_trip:
            price = price * 2
    elif product.luxury:
        price = get_luxury_price(total_traveler_count)
        if round_trip:
            price = price * 2
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
    if date_to:
        round_trip = True

    total_traveler_count = traveler_count_adults + traveler_count_children

    queryset = Product.objects.all()
    if location_from:
        queryset = queryset.filter(pickup_places=location_from) | queryset.filter(pickup_places=None)
    if location_to:
        queryset = queryset.filter(dropoff_places=location_to) | queryset.filter(dropoff_places=None)

    products = FrontPageProduct.objects.filter(bokun_product__in=queryset)
    # unavailable = Product.objects.all().exclude(bokun_id__in=queryset)
    # unavailable_products = FrontPageProduct.objects.filter(bokun_product__in=unavailable)
    reply = []

    for product in products:
        single_product_dict = FrontPageProductSerializer(product).data
        price = get_product_price(product, traveler_count_adults, traveler_count_children, round_trip)
        single_product_dict['total_price'] = price
        availability = None
        if date_from:
            availability = get_data.get_availability(product.bokun_product.bokun_id, date_from)
            single_product_dict['availability'] = availability
        else:
            single_product_dict['availability'] = None
        single_product_dict['available'] = False
        if price and availability:
            for time_slot in availability:
                if time_slot['availability_count'] >= total_traveler_count:
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
            for time_slot in return_availability:
                if time_slot['availability_count'] >= total_traveler_count:
                    single_product_dict['available_return'] = True
                    break
        reply.append(single_product_dict)

    # for product in unavailable_products:
    #     single_product_dict = FrontPageProductSerializer(product).data
    #     single_product_dict['available'] = False
    #     reply.append(single_product_dict)

    return Response(reply)


@api_view(['GET'])
def get_single_frontpage_product(request, **kwargs):
    traveler_count_adults = request.query_params.get('traveler_count_adults', 0) or 0
    traveler_count_adults = int(traveler_count_adults)
    traveler_count_children = request.query_params.get('traveler_count_children', 0) or 0
    traveler_count_children = int(traveler_count_children)
    date_from = request.query_params.get('date_from', None)
    date_to = request.query_params.get('date_to', None)
    round_trip = False
    if date_to:
        round_trip = True
    product = FrontPageProduct.objects.get(id=kwargs['id'])
    data = FrontPageProductSerializer(product).data
    data['total_price'] = get_product_price(product, traveler_count_adults, traveler_count_children, round_trip)
    if date_from:
        availability = get_data.get_availability(product.bokun_product.bokun_id, date_from)
        data['availability'] = availability
    else:
        data['availability'] = None
    if date_to:
        return_availability = get_data.get_availability(product.return_product.bokun_id, date_to)
        data['availability_return'] = return_availability
    else:
        data['availability_return'] = None
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
    phone_number = body.get('phone_number')
    email = body.get('email')
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
                                                 name=name))


@api_view(['POST'])
def remove_extra_from_cart(request):
    body = json.loads(request.body)
    session_id = body['session_id']
    booking_id = body['booking_id']
    extra_id = body['extra_id']
    return Response(get_data.remove_extra_from_cart(session_id, booking_id, extra_id))


@api_view(['POST'])
def payment_info(request):
    body = json.loads(request.body)
    session_id = body['session_id']
    return Response(get_data.get_payment(session_id))
