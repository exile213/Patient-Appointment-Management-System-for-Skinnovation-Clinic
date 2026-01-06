from django.urls import path
from . import views

app_name = 'attendant'

urlpatterns = [
    path('', views.attendant_dashboard, name='dashboard'),
    path('appointments/', views.attendant_appointments, name='appointments'),
    path('appointments/<int:appointment_id>/', views.attendant_appointment_detail, name='appointment_detail'),
    path('appointments/<int:appointment_id>/confirm/', views.attendant_confirm_appointment, name='confirm_appointment'),
    path('appointments/<int:appointment_id>/complete/', views.attendant_complete_appointment, name='complete_appointment'),
    path('patients/<int:patient_id>/', views.attendant_patient_profile, name='patient_profile'),
    path('notifications/', views.attendant_notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.attendant_mark_notification_read, name='mark_notification_read'),
    path('history/', views.attendant_history, name='history'),
    path('feedback/', views.attendant_feedback, name='feedback'),
    path('schedule/', views.attendant_schedule, name='schedule'),
    path('manage-profile/', views.attendant_manage_profile, name='manage_profile'),
    path('leave/request/', views.request_leave, name='request_leave'),
    path('leave/requests/', views.view_leave_requests, name='view_leave_requests'),
    # API endpoints
    path('api/notifications/', views.get_notifications_api, name='get_notifications_api'),
    path('api/notifications/update/', views.update_notifications_api, name='update_notifications_api'),
]
