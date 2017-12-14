from bokun_wrapper import get_data
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Vendor, Place, Product
from .serializers import ProductSerializer, VendorSerializer, PlaceSerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.all()
        pickup_place = self.request.query_params.get('pickup_place', None)
        dropoff_place = self.request.query_params.get('dropoff_place', None)
        if pickup_place:
            queryset = queryset.filter(pickup_places=pickup_place) | queryset.filter(pickup_places=None)
            queryset
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