from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.conf import settings
from django.utils import timezone


class User(AbstractUser):
    """Custom user model that extends Django's AbstractUser"""
    USER_TYPE_CHOICES = [
        ('patient', 'Patient'),
        ('admin', 'Staff'),
        ('owner', 'Owner'),
        ('attendant', 'Attendant'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    CIVIL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('widowed', 'Widowed'),
        ('divorced', 'Divorced'),
        ('separated', 'Separated'),
    ]
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='patient')
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )],
        blank=True
    )
    middle_name = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True, help_text="Complete address")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    civil_status = models.CharField(max_length=10, choices=CIVIL_STATUS_CHOICES, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True, help_text="Age of the user (automatically calculated from birthday)")
    
    def save(self, *args, **kwargs):
        """Override save to automatically calculate age from birthday"""
        if self.birthday:
            from datetime import date
            today = date.today()
            self.age = today.year - self.birthday.year - ((today.month, today.day) < (self.birthday.month, self.birthday.day))
        super().save(*args, **kwargs)
    occupation = models.CharField(max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.middle_name or ''} {self.last_name}".strip()

    class Meta:
        db_table = 'users'


class AttendantProfile(models.Model):
    """Profile model for attendants with work schedule"""
    DAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attendant_profile', limit_choices_to={'user_type': 'attendant'})
    work_days = models.JSONField(default=list, help_text="List of work days (e.g., ['Monday', 'Tuesday', ...])")
    start_time = models.TimeField(default='10:00', help_text="Work start time (e.g., 10:00 AM)")
    end_time = models.TimeField(default='18:00', help_text="Work end time (e.g., 6:00 PM)")
    phone = models.CharField(
        max_length=11,
        validators=[RegexValidator(
            regex=r'^09\d{9}$',
            message="Phone number must be 11 digits starting with 09 (e.g., 09123456789)."
        )],
        blank=True,
        null=True,
        help_text="11-digit phone number starting with 09"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Work Schedule"
    
    class Meta:
        db_table = 'attendant_profiles'


class StoreHours(models.Model):
    """Model for store operating hours"""
    DAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]
    
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    open_time = models.TimeField()
    close_time = models.TimeField()
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.is_closed:
            return f"{self.day_of_week}: Closed"
        return f"{self.day_of_week}: {self.open_time} - {self.close_time}"

    class Meta:
        db_table = 'store_hours'
        verbose_name_plural = 'Store Hours'


class ClosedDates(models.Model):
    """Model for dates when the clinic is closed"""
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.start_date} to {self.end_date} - {self.reason or 'Closed'}"

    class Meta:
        db_table = 'closed_dates'
        verbose_name_plural = 'Closed Dates'


# AttendantLeaveRequest removed: feature deprecated — model intentionally deleted.


class MedicalHistory(models.Model):
    """Model for patient medical history, prescriptions, and diagnoses"""
    DOCUMENT_TYPE_CHOICES = [
        ('medical_history', 'Medical History'),
        ('prescription', 'Prescription'),
        ('diagnosis', 'Diagnosis'),
        ('lab_result', 'Lab Result'),
        ('other', 'Other'),
    ]
    
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='medical_history', limit_choices_to={'user_type': 'patient'})
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES, default='medical_history')
    title = models.CharField(max_length=255, help_text="Title or description of the document")
    file = models.FileField(upload_to='medical_history/%Y/%m/', help_text="Upload medical history, prescription, or diagnosis document")
    notes = models.TextField(blank=True, null=True, help_text="Additional notes about this document")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'medical_history'
        ordering = ['-uploaded_at']
        verbose_name = 'Medical History'
        verbose_name_plural = 'Medical History'
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.get_document_type_display()} - {self.title}"
    
    def get_file_name(self):
        """Get the filename without path"""
        if self.file:
            return self.file.name.split('/')[-1]
        return None
