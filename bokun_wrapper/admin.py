from django.contrib import admin

from .models import FrontPageProduct, Place, Product

admin.site.register(FrontPageProduct)
admin.site.register(Place)
admin.site.register(Product)

