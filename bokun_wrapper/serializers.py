from rest_framework import serializers, fields
from .models import Vendor, Place, Product


class PlaceSerializer(serializers.ModelSerializer):
    location = fields.JSONField()
    json = fields.JSONField()

    class Meta:
        model = Place
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    # pickup_places = PlaceSerializer(many=True)
    # dropoff_places = PlaceSerializer(many=True)

    photos = fields.JSONField()
    bookable_extras = fields.JSONField()
    json = fields.JSONField()

    class Meta:
        model = Product
        fields = '__all__'


class VendorSerializer(serializers.ModelSerializer):
    json = fields.JSONField()

    class Meta:
        model = Vendor
        fields = '__all__'
