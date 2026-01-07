from django.contrib import admin
from .models import Package, PackageBooking, PackageAppointment, PackageService


class PackageServiceInline(admin.TabularInline):
    """Inline admin for PackageService through model"""
    model = PackageService
    extra = 1
    fields = ('service',)
    verbose_name_plural = 'Services in Package'


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    """Admin for Package model"""
    list_display = ('package_name', 'price', 'sessions', 'duration_days', 'grace_period_days', 'services_count')
    list_filter = ('created_at',)
    search_fields = ('package_name', 'description')
    ordering = ('package_name',)
    readonly_fields = ('created_at', 'updated_at', 'services_count')
    inlines = [PackageServiceInline]
    
    def services_count(self, obj):
        """Display count of services in package"""
        return obj.services.count()
    services_count.short_description = 'Services'


@admin.register(PackageBooking)
class PackageBookingAdmin(admin.ModelAdmin):
    """Admin for PackageBooking model"""
    list_display = ('patient', 'package', 'sessions_remaining', 'valid_until', 'created_at')
    list_filter = ('created_at', 'valid_until')
    search_fields = ('patient__first_name', 'patient__last_name', 'package__package_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PackageAppointment)
class PackageAppointmentAdmin(admin.ModelAdmin):
    """Admin for PackageAppointment model"""
    list_display = ('booking', 'attendant', 'appointment_date', 'appointment_time', 'status')
    list_filter = ('status', 'appointment_date', 'created_at')
    search_fields = ('booking__patient__first_name', 'booking__patient__last_name', 'booking__package__package_name')
    ordering = ('-appointment_date', '-appointment_time')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PackageService)
class PackageServiceAdmin(admin.ModelAdmin):
    """Admin for PackageService through model"""
    list_display = ('package', 'service', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('package__package_name', 'service__service_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')