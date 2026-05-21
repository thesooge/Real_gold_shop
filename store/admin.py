from django.contrib import admin

from .models import GoldItem, Order, CartItem, GoldPrice, Coupon, ShippingSettings, Announcement
# Register your models here.

@admin.register(GoldItem)
class GoldItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'weight_gram', 'base_rate_per_gram','profit_percent' , 'stock', 'created_at')

admin.site.register(Order)
admin.site.register(CartItem)
admin.site.register(GoldPrice)

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "discount_percent", "discount_amount", "valid_from", "valid_to", "active")
    list_filter = ("discount_type", "active")
    search_fields = ("code",)


@admin.register(ShippingSettings)
class ShippingSettingsAdmin(admin.ModelAdmin):
    list_display = ("flat_rate", "free_from_amount")    

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("message", "is_active", "created_at")
    list_filter = ("is_active",)
    ordering = ("-created_at",)    