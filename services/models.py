from django.db import models


class ServiceCategory(models.Model):
    """Model for service categories"""
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'service_categories'
        verbose_name_plural = 'Service Categories'


class Service(models.Model):
    """Model for beauty clinic services"""
    service_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    duration = models.IntegerField(help_text="Duration in minutes")
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.service_name

    class Meta:
        db_table = 'services'
        ordering = ['service_name']


class ServiceImage(models.Model):
    """Model for additional service images"""
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='services/images/')
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service.service_name} - Image {self.id}"

    class Meta:
        db_table = 'service_images'
        ordering = ['-is_primary', '-created_at']


class HistoryLog(models.Model):
    """Model for tracking changes to services, products, packages, clinic hours, and closed days"""
    TYPE_CHOICES = [
        ('Service', 'Service'),
        ('Product', 'Product'),
        ('Package', 'Package'),
        ('Clinic Hours', 'Clinic Hours'),
        ('Closed Day', 'Closed Day'),
    ]
    
    ACTION_CHOICES = [
        ('Added', 'Added'),
        ('Edited', 'Edited'),
        ('Deleted', 'Deleted'),
        ('Availed', 'Availed'),
    ]
    
    datetime = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=12, choices=TYPE_CHOICES)
    name = models.CharField(max_length=255)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    performed_by = models.CharField(max_length=255)
    details = models.TextField(blank=True, null=True)
    related_id = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.type} {self.name} - {self.action} by {self.performed_by}"

    class Meta:
        db_table = 'history_log'
        ordering = ['-datetime']