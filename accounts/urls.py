from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Root login selection (for /login/ namespace)
    path('', views.login_selection, name='login_selection'),
    path('patient/', views.patient_login, name='patient_login'),
    path('admin/', views.admin_login, name='admin_login'),
    path('owner/', views.owner_login, name='owner_login'),
    path('attendant/', views.attendant_login, name='attendant_login'),
    
    # Accounts namespace patterns (for /accounts/ namespace)
    # Note: 'login/' pattern is excluded to avoid conflict with allauth's account_login URL
    # Use 'login/patient/', 'login/admin/', etc. for specific login types
    path('login/patient/', views.patient_login, name='patient_login'),
    path('login/admin/', views.admin_login, name='admin_login'),
    path('login/owner/', views.owner_login, name='owner_login'),
    path('login/attendant/', views.attendant_login, name='attendant_login'),
    
    # Common patterns
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('medical-history/', views.medical_history, name='medical_history'),
    path('medical-history/delete/<int:history_id>/', views.delete_medical_history, name='delete_medical_history'),
    path('verify-password/', views.verify_password, name='verify_password'),
    path('test-mailtrap/', views.test_mailtrap, name='test_mailtrap'),
    
    # Password Reset patterns
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # Legacy redirect
    path('login/legacy/', views.login_view, name='login'),
]
