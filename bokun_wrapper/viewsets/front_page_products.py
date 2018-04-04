from django.db.models import Q
from rest_framework import viewsets, serializers
from rest_framework.decorators import api_view, detail_route
# from rest_framework.response import Response

from ..models import Product, ProductBullet

from .products import ProductSerializer


class BulletSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductBullet
        fields = ('icon', 'bullet')


class FrontPageProductSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = kwargs['context']['request']

        if request.query_params.get('is_round_trip', 'false') != 'false':
            self.fields['bokun_product'] = ProductSerializer(source='_discount_product')
        else:
            self.fields['bokun_product'] = ProductSerializer()

    bokun_product = ProductSerializer(source='_bokun_product')

    return_product = ProductSerializer()

    class Meta:
        model = Product
        fields = (
            'id',
            'kind',
            'single_seat_booking',
            'title',
            'excerpt',
            'description',
            'bullets',
            'tagline',
            'photo_path',

            'bokun_product',
            'return_product',
        )


class FrontPageProductViewSet(viewsets.ModelViewSet):
    serializer_class = FrontPageProductSerializer
    queryset = Product.objects.all()\
        .select_related('bokun_product', 'return_product', 'discount_product')\
        .prefetch_related('bullets')

    def get_queryset(self):
        query = self.request.query_params

        traveler_count = int(query.get('traveler_count') or 0)
        direction = query.get('direction')

        if traveler_count:
            count_filters = dict(min_people__lte=traveler_count, max_people__gte=traveler_count)
        else:
            count_filters = dict()

        if direction:
            direction_filters = dict(direction__in=['ANY', direction])
        else:
            direction_filters = dict()

        return super().get_queryset().filter(Q(
            # Private and Luxury:
            kind__in=['PRI', 'LUX'],
            **count_filters
        ) | ~Q(
            kind__in=['PRI', 'LUX']
        ), **direction_filters)
