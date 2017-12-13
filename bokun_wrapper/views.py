from rest_framework import viewsets
from .models import Vendor, Place, Product
from .serializers import ProductSerializer, VendorSerializer, PlaceSerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class PlaceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer


class VendorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
