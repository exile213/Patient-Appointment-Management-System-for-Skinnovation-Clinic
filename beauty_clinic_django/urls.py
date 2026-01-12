"""
URL configuration for beauty_clinic_django project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from appointments.views import get_notifications_api, update_notifications_api
from appointments.cron_views import trigger_appointment_reminders, cron_health_check, cron_debug_appointments

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', include('accounts.urls', namespace='login')),  # Handles /login/ patterns
    # Social auth (django-allauth) - include FIRST to ensure allauth URLs are registered before custom accounts URLs
    # Allauth provides URLs like /accounts/social/google/login/ and expects 'socialaccount_login' URL name
    path('accounts/', include('allauth.urls')),
    # Custom accounts URLs - comes after allauth to avoid conflicts, but custom patterns take precedence
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('services/', include('services.urls')),
    path('products/', include('products.urls')),
    path('packages/', include('packages.urls')),
    path('appointments/', include('appointments.urls')),
    path('analytics/', include('analytics.urls')),
    path('attendant/', include('attendant.urls')),
    path('owner/', include('owner.urls')),
    path('payments/', include('payments.urls')),
    
    # Cron API endpoints for external cron service (cron-job.org)
    path('api/cron/reminders/', trigger_appointment_reminders, name='cron_reminders'),
    path('api/cron/health/', cron_health_check, name='cron_health'),
    path('api/cron/debug-appointments/', cron_debug_appointments, name='cron_debug_appointments'),
    
    # Global notification API endpoints (for pages that don't have their own)
    path('notifications/get_notifications.php', get_notifications_api, name='global_get_notifications'),
    path('notifications/update_notifications.php', update_notifications_api, name='global_update_notifications'),
]

# Serve media and static files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Explicitly serve static files from STATICFILES_DIRS
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
