from django.contrib import admin
from .models import Product, StockHistory


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin for Product model"""
    list_display = ('product_name', 'price', 'stock', 'image_preview', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('product_name', 'description')
    ordering = ('product_name',)
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    fields = ('product_name', 'description', 'price', 'stock', 'product_image', 'image_preview', 'created_at', 'updated_at')
    
    def image_preview(self, obj):
        """Display image preview in admin list"""
        if obj.product_image:
            return f'<img src="{obj.product_image.url}" style="max-height: 50px; max-width: 50px;" />'
        return "No image"
    image_preview.allow_tags = True
    image_preview.short_description = 'Image Preview'


@admin.register(StockHistory)
class StockHistoryAdmin(admin.ModelAdmin):
    """Admin for Stock History model"""
    list_display = ('product', 'action', 'quantity', 'previous_stock', 'new_stock', 'staff', 'created_at')
    list_filter = ('action', 'created_at', 'product')
    search_fields = ('product__product_name', 'staff__first_name', 'staff__last_name', 'reason')
    readonly_fields = ('product', 'action', 'quantity', 'previous_stock', 'new_stock', 'staff', 'reason', 'created_at')
    ordering = ('-created_at',)
    
    def has_add_permission(self, request):
        # Prevent manual creation - history should be auto-generated
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion to maintain audit trail
        return False