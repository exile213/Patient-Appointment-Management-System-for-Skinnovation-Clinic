from django.urls import path
from . import views
from . import sms_views
# leave_views removed; leave management is deprecated
from appointments import admin_views as appointment_admin_views

app_name = 'owner'

urlpatterns = [
    path('', views.owner_dashboard, name='dashboard'),
    path('patients/', views.owner_patients, name='patients'),
    path('patients/<int:patient_id>/', views.owner_view_patient, name='view_patient'),
    path('appointments/', views.owner_appointments, name='appointments'),
    path('appointments/<int:appointment_id>/', views.owner_view_appointment, name='view_appointment'),
    path('appointments/<int:appointment_id>/cancel/', views.owner_cancel_appointment, name='cancel_appointment'),
    path('appointments/<int:appointment_id>/reschedule/', views.owner_reschedule_appointment, name='reschedule_appointment'),
    path('services/', views.owner_services, name='services'),
    path('packages/', views.owner_packages, name='packages'),
    path('products/', views.owner_products, name='products'),
    path('analytics/', views.owner_analytics, name='analytics'),
    # Maintenance
    path('maintenance/', views.owner_maintenance, name='maintenance'),
    # Management functions
    path('manage/services/', views.owner_manage_services, name='manage_services'),
    path('manage/packages/', views.owner_manage_packages, name='manage_packages'),
    path('manage/products/', views.owner_manage_products, name='manage_products'),
    path('manage/patient-profiles/', views.owner_manage_patient_profiles, name='manage_patient_profiles'),
    path('history-log/', views.owner_view_history_log, name='history_log'),
    path('inventory/', views.owner_view_inventory, name='view_inventory'),
    
    # Image Management URLs
    path('manage/service-images/', views.owner_manage_service_images, name='manage_service_images'),
    path('manage/product-images/', views.owner_manage_product_images, name='manage_product_images'),
    path('delete-service-image/<int:image_id>/', views.owner_delete_service_image, name='delete_service_image'),
    path('delete-product-image/<int:image_id>/', views.owner_delete_product_image, name='delete_product_image'),
    path('set-primary-service-image/<int:image_id>/', views.owner_set_primary_service_image, name='set_primary_service_image'),
    path('set-primary-product-image/<int:image_id>/', views.owner_set_primary_product_image, name='set_primary_product_image'),
    
    # SMS functionality
    path('sms-test/', sms_views.sms_test, name='sms_test'),
    path('send-test-sms/', sms_views.send_test_sms, name='send_test_sms'),
    
    # Attendant Management
    path('manage/attendants/', views.owner_manage_attendants, name='manage_attendants'),
    path('manage/attendants/create-user/', views.owner_create_attendant_user, name='create_attendant_user'),
    path('manage/attendants/edit-user/<int:user_id>/', views.owner_edit_attendant_user, name='edit_attendant_user'),
    path('manage/attendants/toggle-user/<int:user_id>/', views.owner_toggle_attendant_user, name='toggle_attendant_user'),
    path('manage/attendants/reset-password/<int:user_id>/', views.owner_reset_attendant_password, name='reset_attendant_password'),
    path('manage/attendants/profile/<int:user_id>/', views.owner_manage_attendant_profile, name='manage_attendant_profile'),
    path('manage/attendants/add/', views.owner_add_attendant, name='add_attendant'),
    path('manage/attendants/delete/<int:attendant_id>/', views.owner_delete_attendant, name='delete_attendant'),
    path('manage/attendants/add-closed-day/', views.owner_add_closed_day, name='add_closed_day'),
    path('manage/attendants/delete-closed-day/<int:closed_day_id>/', views.owner_delete_closed_day, name='delete_closed_day'),
    path('manage/attendants/timeslots/add/', views.owner_add_timeslot, name='add_timeslot'),
    path('manage/attendants/timeslots/<int:timeslot_id>/toggle/', views.owner_toggle_timeslot, name='toggle_timeslot'),
    path('manage/attendants/timeslots/<int:timeslot_id>/delete/', views.owner_delete_timeslot, name='delete_timeslot'),
    
    # Leave Request Management removed (deprecated)
    
    # Notifications and Settings
    path('notifications/', views.owner_notifications, name='notifications'),
    path('notifications/delete/<int:notification_id>/', views.owner_delete_notification, name='delete_notification'),
    path('notifications/mark-read/<int:notification_id>/', views.owner_mark_notification_read, name='mark_notification_read'),
    path('notifications/approve-cancellation/<int:cancellation_request_id>/', views.owner_approve_cancellation, name='approve_cancellation'),
    path('notifications/reject-cancellation/<int:cancellation_request_id>/', views.owner_reject_cancellation, name='reject_cancellation'),
    path('manage/clinic-hours/', views.owner_manage_clinic_hours, name='manage_clinic_hours'),
    
    # Database Backup Management
    path('backup-database/', views.owner_backup_database, name='backup_database'),
    path('backup-database/download/<str:filename>/', views.owner_download_backup, name='download_backup'),
    # Rendered service history (owner access)
    path('service-history/', appointment_admin_views.service_history, name='service_history'),
    path('service-history/<int:pk>/', appointment_admin_views.service_history_detail, name='service_history_detail'),
]
