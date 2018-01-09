from rest_framework import serializers, fields
from .models import Vendor, Place, Product, FrontPageProduct


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


class FrontPageProductSerializer(serializers.ModelSerializer):
    bokun_product = ProductSerializer()
    return_product = ProductSerializer()

    class Meta:
        model = FrontPageProduct
        fields = '__all__'
