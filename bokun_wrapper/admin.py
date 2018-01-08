from django.contrib import admin

from .models import FrontPageProduct, Place, Product


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_editable = ('ordering',)
    list_display = ('title', 'ordering',)
    list_per_page = 10000

admin.site.register(FrontPageProduct)
admin.site.register(Product)

