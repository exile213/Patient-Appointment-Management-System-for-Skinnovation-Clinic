from django.contrib import admin
from .models import ServiceCategory, Service, HistoryLog


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    """Admin for ServiceCategory model"""
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Admin for Service model"""
    list_display = ('service_name', 'category', 'price', 'duration', 'image_preview', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('service_name', 'description')
    ordering = ('service_name',)
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    fields = ('service_name', 'description', 'price', 'duration', 'category', 'image', 'image_preview', 'created_at', 'updated_at')
    
    def image_preview(self, obj):
        """Display image preview in admin list"""
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 50px; max-width: 50px;" />'
        return "No image"
    image_preview.allow_tags = True
    image_preview.short_description = 'Image Preview'


@admin.register(HistoryLog)
class HistoryLogAdmin(admin.ModelAdmin):
    """Admin for HistoryLog model"""
    list_display = ('datetime', 'type', 'name', 'action', 'performed_by')
    list_filter = ('type', 'action', 'datetime')
    search_fields = ('name', 'performed_by', 'details')
    ordering = ('-datetime',)
    readonly_fields = ('datetime',)