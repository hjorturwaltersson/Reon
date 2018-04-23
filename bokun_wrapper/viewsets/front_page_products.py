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


def create_product_getter(direction, hotel_connection=False):
    def get_product(self, obj):
        query = self.context['request'].query_params

        activity = obj.get_activity(
            outbound=(query.get('direction', 'KEF-RVK') != direction),
            round_trip=query.get('is_round_trip', 'false') != 'false',
            hotel_connection=hotel_connection,
        )

        return ProductSerializer(instance=activity).data

    return get_product


class FrontPageProductSerializer(serializers.ModelSerializer):
    bullets = BulletSerializer(many=True)

    bokun_product = serializers.SerializerMethodField()
    get_bokun_product = create_product_getter('KEF-RVK', False)

    return_product = serializers.SerializerMethodField()
    get_return_product = create_product_getter('RVK-KEF', False)

    bokun_product_hc = serializers.SerializerMethodField()
    get_bokun_product_hc = create_product_getter('KEF-RVK', True)

    return_product_hc = serializers.SerializerMethodField()
    get_return_product_hc = create_product_getter('RVK-KEF', True)

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

            'bokun_product_hc',
            'return_product_hc',

            'free_hotel_connection',
        )


class FrontPageProductViewSet(viewsets.ModelViewSet):
    serializer_class = FrontPageProductSerializer
    queryset = Product.objects.all().select_related(
        'activity_inbound',
        'activity_outbound',
        'activity_inbound_rt',
        'activity_outbound_rt',
        'activity_inbound_hc',
        'activity_outbound_hc',
        'activity_inbound_hc_rt',
        'activity_outbound_hc_rt',
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
