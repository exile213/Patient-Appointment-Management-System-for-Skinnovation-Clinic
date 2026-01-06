from django.contrib import admin
from .models import Appointment, Request, CancellationRequest, Feedback, Notification, SMSTemplate, SMSHistory, Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Admin for Room model"""
    list_display = ('name', 'is_available')
    list_filter = ('is_available',)
    search_fields = ('name',)
    list_editable = ('is_available',)
    
    fieldsets = (
        ('Room Information', {
            'fields': ('name', 'is_available')
        }),
    )


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Admin for Appointment model"""
    list_display = ('patient', 'service', 'product', 'package', 'appointment_date', 'appointment_time', 'status')
    list_filter = ('status', 'appointment_date', 'created_at')
    search_fields = ('patient__first_name', 'patient__last_name', 'service__service_name')
    ordering = ('-appointment_date', '-appointment_time')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    """Admin for Request model"""
    list_display = ('patient', 'appointment', 'type', 'status', 'created_at')
    list_filter = ('type', 'status', 'created_at')
    search_fields = ('patient__first_name', 'patient__last_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'admin_response_at')


@admin.register(CancellationRequest)
class CancellationRequestAdmin(admin.ModelAdmin):
    """Admin for CancellationRequest model"""
    list_display = ('patient', 'appointment_type', 'status', 'created_at')
    list_filter = ('appointment_type', 'status', 'created_at')
    search_fields = ('patient__first_name', 'patient__last_name', 'reason')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    """Admin for Feedback model"""
    list_display = ('patient', 'appointment', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('patient__first_name', 'patient__last_name', 'comment')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin for Notification model"""
    list_display = ('title', 'type', 'patient', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'patient__first_name', 'patient__last_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(SMSTemplate)
class SMSTemplateAdmin(admin.ModelAdmin):
    """Admin for SMS Template model"""
    list_display = ('name', 'template_type', 'is_active', 'created_by', 'created_at')
    list_filter = ('template_type', 'is_active', 'created_at')
    search_fields = ('name', 'subject', 'message')
    ordering = ('template_type', 'name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'template_type', 'is_active')
        }),
        ('Message Content', {
            'fields': ('subject', 'message'),
            'description': 'Use variables like {patient_name}, {appointment_date}, {appointment_time}, {service_name}, etc.'
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new template
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SMSHistory)
class SMSHistoryAdmin(admin.ModelAdmin):
    """Admin for SMS History model"""
    list_display = ('phone_number', 'template_used', 'status', 'sent_at', 'sender')
    list_filter = ('status', 'template_used__template_type', 'sent_at')
    search_fields = ('phone_number', 'message', 'sender__first_name', 'sender__last_name')
    ordering = ('-sent_at',)
    readonly_fields = ('sent_at', 'formatted_sent_at', 'time_ago')
    
    fieldsets = (
        ('SMS Details', {
            'fields': ('sender', 'phone_number', 'template_used', 'status')
        }),
        ('Message Content', {
            'fields': ('message',)
        }),
        ('API Response', {
            'fields': ('message_id', 'api_response'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('sent_at', 'formatted_sent_at', 'time_ago'),
            'classes': ('collapse',)
        }),
    )