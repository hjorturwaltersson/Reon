from django.contrib import admin

from .models import Product, ProductBullet, Place, Activity


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_editable = ('ordering',)
    list_display = ('title', 'ordering',)
    list_per_page = 10000


class BulletInline(admin.TabularInline):
    model = ProductBullet
    fields = ('icon', 'image', 'text')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'kind', 'ordering')
    list_editable = ('ordering',)

    raw_id_fields = (
        'activity_inbound',
        'activity_outbound',
        'activity_inbound_rt',
        'activity_outbound_rt',
        'activity_inbound_hc',
        'activity_outbound_hc',
        'activity_inbound_hc_rt',
        'activity_outbound_hc_rt',
    )

    inlines = [
        BulletInline
    ]

admin.site.register(Activity)
