from django.contrib import admin
from .models import Payment, StockMovement, UserActivityLog


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'appointment', 'amount', 'amount_paid', 'payment_status', 'payment_method', 'payment_date']
    list_filter = ['payment_status', 'payment_method', 'payment_date']
    search_fields = ['appointment__patient__first_name', 'appointment__patient__last_name', 'reference_number']
    ordering = ['-created_at']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'movement_type', 'quantity', 'previous_stock', 'new_stock', 'created_at']
    list_filter = ['movement_type', 'created_at']
    search_fields = ['product__product_name', 'reason']
    ordering = ['-created_at']


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'action', 'model_name', 'description', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__username', 'description']
    ordering = ['-timestamp']
