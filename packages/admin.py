from django.contrib import admin
from .models import Package, PackageBooking, PackageAppointment


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    """Admin for Package model"""
    list_display = ('package_name', 'price', 'sessions', 'duration_days', 'grace_period_days')
    list_filter = ('created_at',)
    search_fields = ('package_name', 'description')
    ordering = ('package_name',)
    readonly_fields = ('created_at', 'updated_at')


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