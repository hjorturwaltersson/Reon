"""bokun_wrapper URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

from .views import (
    PlaceViewSet,
    VendorViewSet,
)
from .viewsets import (
    FrontPageProductViewSet,
    ProductViewSet,
)

from .views import get_availability, get_frontpage_products, get_cart, get_single_frontpage_product
from .views import add_to_cart, add_extra_to_cart, pay, remove_extra_from_cart, get_cross_sale, add_cross_sale_to_cart, remove_activity_from_cart
from .views import blue_lagoon_places, blue_lagoon_order, blue_lagoon_order_test

router = routers.DefaultRouter()
router.register('front-page-products', FrontPageProductViewSet)
router.register('products', ProductViewSet)
router.register('places', PlaceViewSet)
router.register('vendors', VendorViewSet)


urlpatterns = [
    url(r'', include(router.urls)),
    path('admin/', admin.site.urls),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'get_availability', get_availability),
    url(r'get_cart', get_cart),
    path(r'get_frontpage_products/<int:id>/', get_single_frontpage_product),
    url(r'get_frontpage_products', get_frontpage_products),
    url(r'add_to_cart', add_to_cart),
    url(r'add_extra_to_cart', add_extra_to_cart),
    url(r'pay', pay),
    url(r'remove_extra_from_cart', remove_extra_from_cart),
    url(r'remove_activity_from_cart', remove_activity_from_cart),
    url(r'add_crosssale_to_cart', add_cross_sale_to_cart),
    url(r'crosssale', get_cross_sale),
    url(r'blp', blue_lagoon_places),
    url(r'blue_lagoon_places', blue_lagoon_places),
    url(r'blue_lagoon_order', blue_lagoon_order),
    url(r'test_blo', blue_lagoon_order_test),

]

urlpatterns += router.urls
