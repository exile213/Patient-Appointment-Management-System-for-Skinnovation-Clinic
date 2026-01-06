from django.db import models
from django.utils import timezone
from accounts.models import User
from appointments.models import Appointment
from services.models import Service
from products.models import Product
from packages.models import Package


class PatientAnalytics(models.Model):
    """Model for storing patient analytics data"""
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics')
    total_appointments = models.IntegerField(default=0)
    completed_appointments = models.IntegerField(default=0)
    cancelled_appointments = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_visit = models.DateTimeField(blank=True, null=True)
    average_visit_frequency = models.IntegerField(default=0, help_text="Days between visits")
    preferred_services = models.JSONField(default=list, blank=True)
    risk_score = models.FloatField(default=0, help_text="Churn risk score (0-1)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.full_name} - Analytics"

    class Meta:
        db_table = 'patient_analytics'
        verbose_name_plural = 'Patient Analytics'


class ServiceAnalytics(models.Model):
    """Model for storing service analytics data"""
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='analytics')
    total_bookings = models.IntegerField(default=0)
    completed_bookings = models.IntegerField(default=0)
    cancelled_bookings = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    average_rating = models.FloatField(default=0)
    popularity_score = models.FloatField(default=0)
    seasonal_trends = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.service.service_name} - Analytics"

    class Meta:
        db_table = 'service_analytics'
        verbose_name_plural = 'Service Analytics'


class BusinessAnalytics(models.Model):
    """Model for storing business-wide analytics"""
    date = models.DateField(unique=True)
    total_appointments = models.IntegerField(default=0)
    completed_appointments = models.IntegerField(default=0)
    cancelled_appointments = models.IntegerField(default=0)
    new_patients = models.IntegerField(default=0)
    returning_patients = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    average_appointment_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    patient_satisfaction_score = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Business Analytics - {self.date}"

    class Meta:
        db_table = 'business_analytics'
        verbose_name_plural = 'Business Analytics'
        ordering = ['-date']


class TreatmentCorrelation(models.Model):
    """Model for storing treatment correlation data"""
    primary_service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='primary_correlations')
    secondary_service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='secondary_correlations')
    correlation_strength = models.FloatField(help_text="Correlation coefficient (-1 to 1)")
    frequency = models.IntegerField(default=0, help_text="Number of times these services were booked together")
    confidence_score = models.FloatField(default=0, help_text="Statistical confidence (0-1)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.primary_service.service_name} ↔ {self.secondary_service.service_name}"

    class Meta:
        db_table = 'treatment_correlations'
        verbose_name_plural = 'Treatment Correlations'
        unique_together = ['primary_service', 'secondary_service']


class PatientSegment(models.Model):
    """Model for patient segmentation"""
    SEGMENT_CHOICES = [
        ('high_value', 'High Value'),
        ('frequent', 'Frequent'),
        ('occasional', 'Occasional'),
        ('at_risk', 'At Risk'),
        ('new', 'New'),
    ]
    
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='segments')
    segment = models.CharField(max_length=20, choices=SEGMENT_CHOICES)
    segment_score = models.FloatField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.full_name} - {self.segment}"

    class Meta:
        db_table = 'patient_segments'
        verbose_name_plural = 'Patient Segments'
