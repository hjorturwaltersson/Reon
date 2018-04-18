from django.db.models import Q
from rest_framework import viewsets, serializers
from rest_framework.decorators import api_view, detail_route
# from rest_framework.response import Response

from ..models import Product, ProductBullet

from .products import ProductSerializer


class BulletSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductBullet
        fields = ('icon', 'image', 'text')


class FrontPageProductSerializer(serializers.ModelSerializer):
    bullets = BulletSerializer(many=True)

    bokun_product = serializers.SerializerMethodField()
    def get_bokun_product(self, obj):
        query = self.context['request'].query_params

        activity = obj.get_activity(
            outbound=(query.get('direction', 'KEF-RVK') != 'KEF-RVK'),
            hotel_connection=query.get('hotel_connection', 'false') != 'false',
            round_trip='return_date' in query,
        )

        return ProductSerializer(instance=activity).data

    return_product = serializers.SerializerMethodField()
    def get_return_product(self, obj):
        query = self.context['request'].query_params

        activity = obj.get_activity(
            outbound=(query.get('direction', 'KEF-RVK') == 'KEF-RVK'),
            hotel_connection=query.get('hotel_connection', 'false') != 'false',
            round_trip='return_date' in query,
        )

        return ProductSerializer(instance=activity).data

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
            'tagline_color',
            'link_url',
            'photo_path',

            'bokun_product',
            'return_product',

            'free_hotel_connection',
        )


class FrontPageProductViewSet(viewsets.ModelViewSet):
    serializer_class = FrontPageProductSerializer
    queryset = Product.objects.all().select_related(
        'activity_inbound',
        'activity_inbound_hc',
        'activity_outbound',
        'activity_outbound_hc',
    ).prefetch_related('bullets')

    def get_queryset(self):
        query = self.request.query_params

        traveler_count = int(query.get('traveler_count') or 0)

        if traveler_count:
            count_filters = dict(min_people__lte=traveler_count, max_people__gte=traveler_count)
        else:
            count_filters = dict()

        return super().get_queryset().filter(Q(
            # Private and Luxury:
            kind__in=['PRI', 'LUX'],
            **count_filters
        ) | ~Q(
            kind__in=['PRI', 'LUX']
        ))
