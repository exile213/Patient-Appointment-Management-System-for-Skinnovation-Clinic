from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment management
    path('list/', views.payment_list, name='payment_list'),
    path('add/<int:appointment_id>/', views.add_payment, name='add_payment'),
    
    # Reports
    path('reports/revenue/', views.generate_revenue_report_pdf, name='revenue_report_pdf'),
    path('reports/patient/<int:patient_id>/', views.generate_patient_history_pdf, name='patient_history_pdf'),
    
    # Stock management
    path('stock/movements/', views.stock_movement_list, name='stock_movement_list'),
    path('stock/alerts/', views.low_stock_alerts, name='low_stock_alerts'),
    
    # Activity logs
    path('logs/activity/', views.user_activity_log_list, name='activity_log_list'),
]
