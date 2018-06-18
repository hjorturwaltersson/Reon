from operator import itemgetter

import arrow
from rest_framework import viewsets, serializers
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from ..get_data import bokun_api
from ..models import Activity


class ProductSerializer(serializers.ModelSerializer):
    vendor = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Activity
        fields = (
            'id',
            'external_id',
            'title',
            'vendor',
            'default_price_category',
            'child_price_category',
            'extras',
            'places',
        )


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ProductSerializer

    @detail_route(methods=['get'])
    def availability(self, request, pk=None):
        return Response(self.get_object().get_availability(request.query_params['date']))
