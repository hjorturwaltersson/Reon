from rest_framework import serializers
from .models import Vendor, Place, Product


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    pickup_places = PlaceSerializer(many=True)
    dropoff_places = PlaceSerializer(many=True)

    class Meta:
        model = Product
        fields = '__all__'


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'

