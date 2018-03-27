from django.db.models import Q
from rest_framework import viewsets, serializers
from rest_framework.decorators import api_view, detail_route
# from rest_framework.response import Response

from ..models import FrontPageProduct

from .products import ProductSerializer


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
        model = FrontPageProduct
        fields = (
            'id',
            'title',
            'excerpt',
            'description',
            'tagline',
            'photo_path',

            'bokun_product',
            'return_product',
        )


class FrontPageProductViewSet(viewsets.ModelViewSet):
    serializer_class = FrontPageProductSerializer
    queryset = FrontPageProduct.objects.all()

    def get_queryset(self):
        query = self.request.query_params

        traveler_count = int(query.get('traveler_count') or 0)

        return super().get_queryset().filter(Q(
            # Private and Luxury:
            Q(private=True) | Q(luxury=True),
            min_people__lte=traveler_count,
            max_people__gte=traveler_count,
        ) | Q(
            # Economy:
            private=False,
            luxury=False,
        ), direction__in=['ANY', query.get('direction')])
