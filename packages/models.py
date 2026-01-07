from django.db import models
from django.conf import settings
from accounts.models import User


class Package(models.Model):
    """Model for beauty clinic packages"""
    package_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sessions = models.IntegerField()
    duration_days = models.IntegerField(help_text="Duration in days")
    grace_period_days = models.IntegerField(help_text="Grace period in days")
    archived = models.BooleanField(default=False)
    services = models.ManyToManyField('services.Service', related_name='packages', blank=True, through='PackageService')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.package_name

    class Meta:
        db_table = 'packages'
        ordering = ['package_name']


class PackageBooking(models.Model):
    """Model for package bookings"""
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='package_bookings')
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='bookings')
    sessions_remaining = models.IntegerField(blank=True, null=True)
    valid_until = models.DateField(blank=True, null=True)
    grace_period_until = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.full_name} - {self.package.package_name}"

    class Meta:
        db_table = 'package_bookings'


class PackageAppointment(models.Model):
    """Model for package appointments"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    booking = models.ForeignKey(PackageBooking, on_delete=models.CASCADE, related_name='appointments')
    attendant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='package_appointments', limit_choices_to={'user_type': 'attendant'})
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.booking.patient.full_name} - {self.appointment_date} {self.appointment_time}"

    class Meta:
        db_table = 'package_appointments'


class PackageService(models.Model):
    """Through model for Package-Service relationship"""
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='package_services')
    service = models.ForeignKey('services.Service', on_delete=models.CASCADE, related_name='service_packages')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.package.package_name} - {self.service.service_name}"

    class Meta:
        db_table = 'package_services'
        unique_together = ('package', 'service')