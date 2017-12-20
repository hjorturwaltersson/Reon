from bokun_wrapper import get_data
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Vendor, Place, Product, FrontPageProduct
from .serializers import ProductSerializer, VendorSerializer, PlaceSerializer, FrontPageProductSerializer


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
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer


class VendorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer


@api_view(['GET'])
def get_availability(request):
    product_id = request.query_params['product_id']
    date = request.query_params['date']
    return Response(get_data.get_availability(product_id, date))


@api_view(['POST'])
def add_to_cart(request):
    product_type_id = request.body['product_type_id']
    start_time_id = request.body['start_time_id']
    date = request.body['date']
    pricing_category_bookings = request.body['pricing_category_bookings']
    session_id = request.body.get('session_id', None)
    pickup_place_id = request.body['pickup_place_id']
    dropoff_place_id = request.body['dropoff_place_id']
    extras = request.body['extras']
    round_trip = request.body['round_trip']
    blue_lagoon = request.body['blue_lagoon']
    return_start_time_id = request.body.get('return_start_time_id', None)
    return_date = request.body.get('return_date', None)
    product = FrontPageProduct.objects.get(id=product_type_id)
    reply = get_data.add_to_cart(activity_id=product.bokun_product.bokun_id,
                                 start_time_id=start_time_id,
                                 date=date,
                                 pricing_category_bookings=pricing_category_bookings,
                                 session_id=session_id,
                                 dropoff_place_id=dropoff_place_id,
                                 pickup_place_id=pickup_place_id,
                                 extras=extras)
    return Response(reply)


@api_view(['POST'])
def add_extra_to_cart(request):
    session_id = request.body['session_id']
    booking_id = request.body['booking_id']
    extra_id = request.body['extra_id']
    unit_count = request.body['unit_count']
    return Response(get_data.add_or_update_extra(session_id, booking_id, extra_id, unit_count))


@api_view(['GET'])
def get_frontpage_products(request):
    traveler_count_adults = request.query_params.get('traveler_count_adults', 0)
    traveler_count_adults = int(traveler_count_adults)
    traveler_count_teenagers = request.query_params.get('traveler_count_teenagers', 0)
    traveler_count_teenagers = int(traveler_count_teenagers)
    location_from = request.query_params['location_from']
    location_to = request.query_params.get('location_to', None)
    date_from = request.query_params.get('date_from', None)
    date_to = request.query_params.get('date_to', None)

    queryset = Product.objects.all()
    if location_from:
        queryset = queryset.filter(pickup_places=location_from) | queryset.filter(pickup_places=None)
    if location_to:
        queryset = queryset.filter(dropoff_places=location_to) | queryset.filter(dropoff_places=None)

    products = FrontPageProduct.objects.filter(bokun_product__in=queryset)
    reply = []

    for product in products:
        single_product_dict = FrontPageProductSerializer(product).data
        price = traveler_count_adults * product.adult_price + traveler_count_teenagers * product.teenager_price
        single_product_dict['total_price'] = price
        if date_from:
            availability = get_data.get_availability(product.bokun_product.bokun_id, date_from)
            single_product_dict['availability'] = availability
        else:
            single_product_dict['availability'] = None
        if date_to:
            return_availability = get_data.get_availability(product.bokun_product.bokun_id, date_to)
            single_product_dict['availability_return'] = return_availability
        else:
            single_product_dict['availability_return'] = None
        reply.append(single_product_dict)

    return Response(reply)


@api_view(['GET'])
def get_single_frontpage_product(request, **kwargs):
    traveler_count_adults = request.query_params.get('traveler_count_adults', 0)
    traveler_count_adults = int(traveler_count_adults)
    traveler_count_teenagers = request.query_params.get('traveler_count_teenagers', 0)
    traveler_count_teenagers = int(traveler_count_teenagers)
    product = FrontPageProduct.objects.get(id=kwargs['id'])
    data = FrontPageProductSerializer(product).data
    price = traveler_count_adults * product.adult_price + traveler_count_teenagers * product.teenager_price
    data['total_price'] = price
    return Response(data)


@api_view(['GET'])
def get_cart(request):
    session_id = request.query_params.get('session_id', None)
    return Response(get_data.get_cart(session_id))

