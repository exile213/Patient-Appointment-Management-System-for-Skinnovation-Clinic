from django.urls import path
from . import views
from . import admin_views
from . import admin_sms_views
from . import template_views

app_name = 'appointments'

urlpatterns = [
    # Patient URLs
    path('', views.my_appointments, name='my_appointments'),
    path('book/service/<int:service_id>/', views.book_service, name='book_service'),
    path('book/product/<int:product_id>/', views.book_product, name='book_product'),
    path('book/package/<int:package_id>/', views.book_package, name='book_package'),
    path('notifications/', views.notifications, name='notifications'),
    path('request-cancellation/<int:appointment_id>/', views.request_cancellation, name='request_cancellation'),
    path('request-reschedule/<int:appointment_id>/', views.request_reschedule, name='request_reschedule'),
    path('submit-feedback/<int:appointment_id>/', views.submit_feedback, name='submit_feedback'),
    path('history/', views.patient_history, name='patient_history'),
    path('unavailable-attendant/<int:appointment_id>/', views.handle_unavailable_attendant, name='handle_unavailable_attendant'),
    
    # API endpoints for unavailability workflow
    path('api/unavailability-details/<int:appointment_id>/', views.api_unavailability_details, name='api_unavailability_details'),
    path('api/available-attendants/', views.api_available_attendants, name='api_available_attendants'),
    path('unavailable/<int:unavailability_request_id>/respond/', views.respond_to_unavailable_attendant, name='respond_to_unavailable_attendant'),
    
    # API endpoints for notifications
    path('notifications/get_notifications.php', views.get_notifications_api, name='get_notifications_api'),
    path('notifications/update_notifications.php', views.update_notifications_api, name='update_notifications_api'),
    
    # Admin URLs
    path('admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin/maintenance/', admin_views.admin_maintenance, name='admin_maintenance'),
    path('admin/seed-diagnoses/', admin_views.admin_seed_diagnoses, name='admin_seed_diagnoses'),
    # Backfill endpoint temporarily disabled (commented out)
    # path('admin/backfill-transaction-ids/', admin_views.admin_backfill_transaction_ids, name='admin_backfill_transaction_ids'),
    path('admin/manage-services/', admin_views.admin_manage_services, name='admin_manage_services'),
    path('admin/manage-packages/', admin_views.admin_manage_packages, name='admin_manage_packages'),
    path('admin/manage-products/', admin_views.admin_manage_products, name='admin_manage_products'),
    path('admin/appointments/', admin_views.admin_appointments, name='admin_appointments'),
    path('admin/patients/', admin_views.admin_patients, name='admin_patients'),
    path('admin/patient/<int:patient_id>/history/', admin_views.patient_history, name='patient_history'),
    path('admin/notifications/', admin_views.admin_notifications, name='admin_notifications'),
    path('admin/settings/', admin_views.admin_settings, name='admin_settings'),
    path('admin/appointment/<int:appointment_id>/', admin_views.admin_appointment_detail, name='admin_appointment_detail'),
    path('admin/appointment/<int:appointment_id>/reassign/', admin_views.admin_reassign_attendant, name='admin_reassign_attendant'),
    path('admin/appointment/<int:appointment_id>/send-sms/', admin_views.admin_send_sms, name='admin_send_sms'),
    path('admin/appointment/<int:appointment_id>/mark-unavailable/', admin_views.admin_mark_attendant_unavailable, name='admin_mark_attendant_unavailable'),
    path('admin/confirm/<int:appointment_id>/', admin_views.admin_confirm_appointment, name='admin_confirm'),
    path('admin/complete/<int:appointment_id>/', admin_views.admin_complete_appointment, name='admin_complete'),
    path('admin/cancel/<int:appointment_id>/', admin_views.admin_cancel_appointment, name='admin_cancel'),
    path('admin/delete/<int:appointment_id>/', admin_views.admin_delete_appointment, name='admin_delete_appointment'),
    path('admin/mark-no-show/<int:appointment_id>/', admin_views.admin_mark_no_show, name='admin_mark_no_show'),
    # Rendered service history
    path('admin/service-history/', admin_views.service_history, name='service_history'),
    path('admin/service-history/<int:pk>/', admin_views.service_history_detail, name='service_history_detail'),
    
    # Additional Admin URLs
    path('admin/add-attendant/', admin_views.admin_add_attendant, name='admin_add_attendant'),
    path('admin/delete-attendant/<int:attendant_id>/', admin_views.admin_delete_attendant, name='admin_delete_attendant'),
    path('admin/attendant-users/create/', admin_views.admin_create_attendant_user, name='admin_create_attendant_user'),
    path('admin/attendant-users/<int:user_id>/edit/', admin_views.admin_edit_attendant_user, name='admin_edit_attendant_user'),
    path('admin/attendant-users/<int:user_id>/toggle/', admin_views.admin_toggle_attendant_user, name='admin_toggle_attendant_user'),
    path('admin/attendant-users/<int:user_id>/reset-password/', admin_views.admin_reset_attendant_password, name='admin_reset_attendant_password'),
    path('admin/attendant-users/<int:user_id>/profile/', admin_views.admin_manage_attendant_profile, name='admin_manage_attendant_profile'),
    path('admin/delete-notification/<int:notification_id>/', admin_views.admin_delete_notification, name='admin_delete_notification'),
    
    # Admin Image Management URLs
    path('admin/manage-service-images/', admin_views.admin_manage_service_images, name='admin_manage_service_images'),
    path('admin/manage-product-images/', admin_views.admin_manage_product_images, name='admin_manage_product_images'),
    path('admin/delete-service-image/<int:image_id>/', admin_views.admin_delete_service_image, name='admin_delete_service_image'),
    path('admin/delete-all-service-images/<int:service_id>/', admin_views.admin_delete_all_service_images, name='admin_delete_all_service_images'),
    path('admin/keep-one-image-per-service/', admin_views.admin_keep_one_image_per_service, name='admin_keep_one_image_per_service'),
    path('admin/delete-product-image/<int:image_id>/', admin_views.admin_delete_product_image, name='admin_delete_product_image'),
    path('admin/set-primary-service-image/<int:image_id>/', admin_views.admin_set_primary_service_image, name='admin_set_primary_service_image'),
    path('admin/set-primary-product-image/<int:image_id>/', admin_views.admin_set_primary_product_image, name='admin_set_primary_product_image'),
    path('admin/patient/<int:patient_id>/', admin_views.admin_view_patient, name='admin_view_patient'),
    path('admin/edit-patient/<int:patient_id>/', admin_views.admin_edit_patient, name='admin_edit_patient'),
    path('admin/delete-patient/<int:patient_id>/', admin_views.admin_delete_patient, name='admin_delete_patient'),
    path('admin/add-closed-day/', admin_views.admin_add_closed_day, name='admin_add_closed_day'),
    path('admin/delete-closed-day/<int:closed_day_id>/', admin_views.admin_delete_closed_day, name='admin_delete_closed_day'),
    path('admin/timeslots/add/', admin_views.admin_add_timeslot, name='admin_add_timeslot'),
    path('admin/timeslots/<int:timeslot_id>/toggle/', admin_views.admin_toggle_timeslot, name='admin_toggle_timeslot'),
    path('admin/timeslots/<int:timeslot_id>/delete/', admin_views.admin_delete_timeslot, name='admin_delete_timeslot'),
    path('admin/packages/<int:package_id>/edit/', admin_views.admin_edit_package_config, name='admin_edit_package_config'),
    path('admin/cancellation-requests/', admin_views.admin_cancellation_requests, name='admin_cancellation_requests'),
    path('admin/approve-cancellation/<int:request_id>/', admin_views.admin_approve_cancellation, name='admin_approve_cancellation'),
    path('admin/reject-cancellation/<int:request_id>/', admin_views.admin_reject_cancellation, name='admin_reject_cancellation'),
    path('admin/approve-reschedule/<int:request_id>/', admin_views.admin_approve_reschedule, name='admin_approve_reschedule'),
    path('admin/reject-reschedule/<int:request_id>/', admin_views.admin_reject_reschedule, name='admin_reject_reschedule'),
    path('admin/inventory/', admin_views.admin_inventory, name='admin_inventory'),
    path('admin/inventory/update/<int:product_id>/', admin_views.admin_update_stock, name='admin_update_stock'),
    path('admin/feedback/', admin_views.admin_view_feedback, name='admin_view_feedback'),
    path('admin/history-log/', admin_views.admin_history_log, name='admin_history_log'),
    path('admin/analytics/', admin_views.admin_analytics, name='admin_analytics'),
    path('admin/rooms/', admin_views.admin_rooms, name='admin_rooms'),
    path('admin/rooms/add/', admin_views.admin_add_room, name='admin_add_room'),
    path('admin/rooms/<int:room_id>/edit/', admin_views.admin_edit_room, name='admin_edit_room'),
    path('admin/rooms/<int:room_id>/delete/', admin_views.admin_delete_room, name='admin_delete_room'),
    path('admin/rooms/<int:room_id>/toggle/', admin_views.admin_toggle_room, name='admin_toggle_room'),
    
    # Admin SMS Testing URLs
    path('admin/sms-test/', admin_sms_views.admin_sms_test, name='admin_sms_test'),
    path('admin/send-test-sms/', admin_sms_views.admin_send_test_sms, name='admin_send_test_sms'),
]
