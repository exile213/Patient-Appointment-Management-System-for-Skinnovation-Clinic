from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, StoreHours, ClosedDates


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for User model"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone', 'middle_name', 'archived')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone', 'middle_name', 'email')}),
    )


@admin.register(StoreHours)
class StoreHoursAdmin(admin.ModelAdmin):
    """Admin for StoreHours model"""
    list_display = ('day_of_week', 'open_time', 'close_time', 'is_closed')
    list_filter = ('is_closed', 'day_of_week')
    ordering = ('day_of_week',)


@admin.register(ClosedDates)
class ClosedDatesAdmin(admin.ModelAdmin):
    """Admin for ClosedDates model"""
    list_display = ('start_date', 'end_date', 'reason', 'created_at')
    list_filter = ('start_date', 'end_date')
    search_fields = ('reason',)
    ordering = ('-start_date',)