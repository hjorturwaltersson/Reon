from django.contrib import admin

from .models import FrontPageProduct, Place, Product


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_editable = ('ordering',)
    list_display = ('title', 'ordering',)
    list_per_page = 10000


@admin.register(FrontPageProduct)
class FrontPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'direction', 'ordering')
    list_editable = ('ordering',)

admin.site.register(Product)

