from operator import itemgetter

import arrow
from rest_framework import viewsets, serializers
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from ..get_data import bokun_api
from ..models import Product


class ProductSerializer(serializers.ModelSerializer):
    vendor = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Product
        fields = (
            'id',
            'external_id',
            'title',
            'vendor',
            'pickup_places',
            'dropoff_places',
            'default_price_category',
            'child_price_category',
            'extras',
        )


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    @detail_route(methods=['get'])
    def availability(self, request, pk=None):
        return Response(self.get_object().get_availability(request.query_params['date']))
