from django.contrib import admin

from .models import FrontPageProduct, FrontPageProductBullet, Place, Product


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_editable = ('ordering',)
    list_display = ('title', 'ordering',)
    list_per_page = 10000


class BulletInline(admin.TabularInline):
    model = FrontPageProductBullet
    fields = ('icon', 'text')


@admin.register(FrontPageProduct)
class FrontPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'kind', 'direction', 'ordering')
    list_editable = ('ordering',)

    raw_id_fields = ('bokun_product', 'discount_product', 'return_product')

    inlines = [
        BulletInline
    ]

admin.site.register(Product)
