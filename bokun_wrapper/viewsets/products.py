from operator import itemgetter

import arrow
from rest_framework import viewsets, serializers
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from ..get_data import bokun_api
from ..models import Product


class ProductSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='bokun_id')
    bookable_extras = serializers.JSONField()
    json = serializers.JSONField()

    class Meta:
        model = Product
        fields = '__all__'


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    @detail_route(methods=['get'])
    def availability(self, request, pk=None):
        date = arrow.get(request.query_params['date'])

        availabilities = bokun_api.get('/activity.json/%s/availabilities' % pk, {
            'start': date.format('YYYY-MM-DD'),
            'end': date.shift(days=1).format('YYYY-MM-DD'),
            'includeSoldOut': True,
        }).json()

        # I don't trust Bokun to sort this properly:
        availabilities.sort(key=itemgetter('date', 'startTime'))

        def makeCategoryPrices(a):
            prices = a['pricesByCategory'].values()
            return {
                'ADULT': int(max(prices)),
                'CHILD': int(min(prices)),
            }

        return Response([{
            'id': a['startTimeId'],
            'date': arrow.get(a['date'] / 1000).format('YYYY-MM-DD'),
            'time': a['startTime'],
            'available': 0 if (a['soldOut'] or a['unavailable']) else a['availabilityCount'],
            'categoryPrices': makeCategoryPrices(a),
            'extraPrices': {int(id): int(price) for id, price in a['extraPrices'].items()},
        } for a in availabilities])
