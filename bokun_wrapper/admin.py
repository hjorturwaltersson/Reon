from django.contrib import admin

from .models import Product, ProductBullet, Place, Activity


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_editable = ('ordering',)
    list_display = ('title', 'ordering',)
    list_per_page = 10000


class BulletInline(admin.TabularInline):
    model = ProductBullet
    fields = ('icon', 'text')


@admin.register(Product)
class FrontPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'kind', 'direction', 'ordering')
    list_editable = ('ordering',)

    raw_id_fields = ('bokun_product', 'discount_product', 'return_product')

    inlines = [
        BulletInline
    ]

admin.site.register(Activity)
