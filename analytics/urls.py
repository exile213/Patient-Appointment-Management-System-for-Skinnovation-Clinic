from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.analytics_dashboard, name='dashboard'),
    path('api/', views.analytics_api, name='api'),
    path('patients/', views.patient_analytics, name='patient_analytics'),
    path('services/', views.service_analytics, name='service_analytics'),
    path('correlations/', views.treatment_correlations, name='treatment_correlations'),
    path('insights/', views.business_insights, name='business_insights'),
    path('feedback/', views.feedback_analytics, name='feedback_analytics'),
]
