from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta

class Room(models.Model):
    """Model for managing rooms available for appointments"""
    name = models.CharField(max_length=100, help_text="Name or number of the room")
    is_available = models.BooleanField(default=True, help_text="Whether the room is currently available for booking")
    
    class Meta:
        db_table = 'rooms'
        ordering = ['name']
        verbose_name = 'Room'
        verbose_name_plural = 'Rooms'
    
    def __str__(self):
        return f"Room {self.name} - {'Available' if self.is_available else 'Unavailable'}"


class Appointment(models.Model):
    """
    Appointment model for managing bookings and scheduling.
    
    STATUS FLOW DOCUMENTATION:
    - All patient bookings (services, products, packages) start as 'scheduled' status
    - 'scheduled' means initially booked, pending staff confirmation
    - Staff must review and confirm bookings to change status from 'scheduled' to 'confirmed'
    - 'pending' status is used for appointments awaiting further action or approval
    - 'rescheduled' status is used when appointment is moved to a different time
    - 'cancelled' status is used when appointments are cancelled
    - 'completed' status is set when attendant marks appointment as finished
    - Additional status flows:
      1. When attendant requests sick leave
      2. Owner approves the leave request
      3. System creates AttendantUnavailabilityRequest for affected appointments
      4. Patient chooses one of 3 options (reschedule, choose another, cancel)
    - See AttendantLeaveRequest and AttendantUnavailabilityRequest models for leave workflow
    """
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rescheduled', 'Rescheduled'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='scheduled')
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], help_text="Quantity of product ordered (for product appointments only)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Foreign Keys
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments')
    attendant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_appointments', limit_choices_to={'user_type': 'attendant'})
    service = models.ForeignKey('services.Service', on_delete=models.CASCADE, related_name='appointments', blank=True, null=True)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='appointments', blank=True, null=True)
    package = models.ForeignKey('packages.Package', on_delete=models.CASCADE, related_name='appointments', blank=True, null=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='appointments', blank=True, null=True)
    
    class Meta:
        db_table = 'appointments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Appointment {self.id} - {self.patient.get_full_name()}"
    
    def get_service_name(self):
        """Get the name of the service, product, or package"""
        if self.service:
            return self.service.service_name
        elif self.product:
            return self.product.product_name
        elif self.package:
            return self.package.package_name
        else:
            return "No service assigned"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class CancellationRequest(models.Model):
    """Cancellation request model"""
    APPOINTMENT_TYPE_CHOICES = [
        ('regular', 'Regular'),
        ('package', 'Package'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    appointment_id = models.IntegerField()
    appointment_type = models.CharField(max_length=10, choices=APPOINTMENT_TYPE_CHOICES)
    reason = models.TextField(blank=True, null=True, help_text='Reason for cancellation (required when cancelling)')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Foreign Keys
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cancellation_requests')
    
    class Meta:
        db_table = 'cancellation_requests'
    
    def __str__(self):
        return f"Cancellation Request {self.id} - {self.patient.get_full_name()}"

class RescheduleRequest(models.Model):
    """Reschedule request model"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    appointment_id = models.IntegerField()
    new_appointment_date = models.DateField()
    new_appointment_time = models.TimeField()
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Foreign Keys
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reschedule_requests')
    
    class Meta:
        db_table = 'reschedule_requests'
    
    def __str__(self):
        return f"Reschedule Request {self.id} - {self.patient.get_full_name()}"

class Feedback(models.Model):
    """Feedback model"""
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], help_text="Rating from 1 to 5 stars for appointment")
    attendant_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], help_text="Rating from 1 to 5 stars for attendant", blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Foreign Keys
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='feedback')
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feedback')
    
    class Meta:
        db_table = 'feedback'
        unique_together = ['appointment', 'patient']  # One feedback per appointment per patient
    
    def __str__(self):
        return f"Feedback {self.id} - Rating: {self.rating}/5"

class Notification(models.Model):
    """Notification model"""
    TYPE_CHOICES = [
        ('appointment', 'Appointment'),
        ('package', 'Package'),
        ('confirmation', 'Confirmation'),
        ('cancellation', 'Cancellation'),
        ('reschedule', 'Reschedule'),
        ('system', 'System'),
    ]
    
    type = models.CharField(max_length=15, choices=TYPE_CHOICES)
    appointment_id = models.IntegerField(blank=True, null=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Foreign Keys
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications', blank=True, null=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification {self.id} - {self.title}"

class Request(models.Model):
    """Request model"""
    TYPE_CHOICES = [
        ('reschedule', 'Reschedule'),
        ('cancellation', 'Cancellation'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
    ]
    
    type = models.CharField(max_length=15, choices=TYPE_CHOICES)
    requested_date = models.DateField(blank=True, null=True)
    requested_time = models.TimeField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    admin_response_at = models.DateTimeField(blank=True, null=True)
    
    # Foreign Keys
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='requests')
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requests')
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='admin_requests', blank=True, null=True)
    
    class Meta:
        db_table = 'requests'
    
    def __str__(self):
        return f"Request {self.id} - {self.type}"

class AttendantUnavailabilityRequest(models.Model):
    """Model for attendant unavailability requests - triggers patient 3-option flow"""
    STATUS_CHOICES = [
        ('pending', 'Pending Patient Response'),
        ('resolved', 'Resolved'),
    ]
    
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='unavailability_requests')
    reason = models.TextField(help_text="Reason for unavailability (e.g., sick leave)")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    patient_choice = models.CharField(
        max_length=20,
        choices=[
            ('choose_another', 'Choose Another Attendant'),
            ('reschedule_same', 'Reschedule with Same Attendant'),
            ('cancel', 'Cancel Appointment'),
        ],
        blank=True,
        null=True
    )
    resolved_at = models.DateTimeField(blank=True, null=True)
    pending_reassignment_choice = models.BooleanField(
        default=True,
        help_text="True if patient needs to make a selection, False after choice is made"
    )
    
    class Meta:
        db_table = 'attendant_unavailability_requests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Unavailability Request for Appointment {self.appointment.id}"


class ClosedDay(models.Model):
    """Closed day model"""
    date = models.DateField(unique=True)
    reason = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'closed_days'
        ordering = ['-date']
    
    def __str__(self):
        return f"Closed Day - {self.date}"

class SMSTemplate(models.Model):
    """SMS Template model for customizable message templates"""
    TEMPLATE_TYPE_CHOICES = [
        ('scheduled', 'Appointment Scheduled (Pending Confirmation)'),
        ('confirmation', 'Appointment Confirmation'),
        ('reminder', 'Appointment Reminder'),
        ('cancellation', 'Cancellation Notification'),
        ('package_confirmation', 'Package Confirmation'),
        ('attendant_reassignment', 'Attendant Reassignment'),
        ('attendant_assignment', 'Attendant Assignment'),
        ('custom', 'Custom Template'),
    ]
    
    name = models.CharField(max_length=100, help_text="Template name for easy identification")
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPE_CHOICES)
    subject = models.CharField(max_length=200, blank=True, help_text="Optional subject line")
    message = models.TextField(help_text="Message template with variables like {patient_name}, {appointment_date}, {appointment_time}, {service_name}")
    is_active = models.BooleanField(default=True, help_text="Whether this template is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_sms_templates')
    
    class Meta:
        db_table = 'sms_templates'
        ordering = ['template_type', 'name']
        unique_together = ['template_type', 'name']
        verbose_name = 'SMS Template'
        verbose_name_plural = 'SMS Templates'
    
    def __str__(self):
        return f"{self.get_template_type_display()} - {self.name}"
    
    def get_available_variables(self):
        """Return list of available variables for this template type"""
        variables = {
            'scheduled': [
                '{patient_name}', '{appointment_date}', '{appointment_time}', 
                '{service_name}', '{clinic_name}', '{clinic_phone}', '{clinic_address}'
            ],
            'confirmation': [
                '{patient_name}', '{appointment_date}', '{appointment_time}', 
                '{service_name}', '{attendant_name}', '{clinic_name}', '{clinic_phone}', '{clinic_address}'
            ],
            'reminder': [
                '{patient_name}', '{appointment_date}', '{appointment_time}', 
                '{service_name}', '{clinic_name}', '{clinic_phone}'
            ],
            'cancellation': [
                '{patient_name}', '{appointment_date}', '{appointment_time}', 
                '{service_name}', '{cancellation_reason}', '{clinic_name}', '{clinic_phone}'
            ],
            'package_confirmation': [
                '{patient_name}', '{package_name}', '{package_price}', 
                '{package_sessions}', '{package_duration}', '{clinic_name}', '{clinic_phone}'
            ],
            'attendant_reassignment': [
                '{patient_name}', '{appointment_date}', '{appointment_time}',
                '{service_name}', '{attendant_name}', '{previous_attendant_name}',
                '{clinic_name}', '{clinic_phone}'
            ],
            'attendant_assignment': [
                '{attendant_name}', '{patient_name}', '{appointment_date}', '{appointment_time}',
                '{service_name}', '{clinic_name}', '{clinic_phone}'
            ],
            'custom': [
                '{patient_name}', '{appointment_date}', '{appointment_time}', 
                '{service_name}', '{package_name}', '{clinic_name}', '{clinic_phone}', '{clinic_address}'
            ]
        }
        return variables.get(self.template_type, variables['custom'])

class SMSHistory(models.Model):
    """Model to store SMS sending history"""
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_sms')
    phone_number = models.CharField(max_length=15)
    message = models.TextField()
    template_used = models.ForeignKey(SMSTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_messages')
    status = models.CharField(max_length=20, choices=[
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('pending', 'Pending')
    ], default='sent')
    message_id = models.CharField(max_length=100, blank=True, null=True)
    api_response = models.JSONField(blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sms_history'
        ordering = ['-sent_at']
        verbose_name = 'SMS History'
        verbose_name_plural = 'SMS Histories'
    
    def __str__(self):
        return f"SMS to {self.phone_number} - {self.sent_at.strftime('%Y-%m-%d %I:%M %p')}"
    
    @property
    def formatted_sent_at(self):
        """Return formatted timestamp"""
        return self.sent_at.strftime('%Y-%m-%d %I:%M:%S %p')
    
    @property
    def time_ago(self):
        """Return human-readable time ago"""
        now = timezone.now()
        diff = now - self.sent_at
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"

class HistoryLog(models.Model):
    """Model to track history of add/edit/archive actions for services, products, packages, and appointments"""
    ACTION_CHOICES = [
        ('add', 'Add'),
        ('edit', 'Edit'),
        ('archive', 'Archive'),
        ('book', 'Book'),
        ('confirm', 'Confirm'),
        ('cancel', 'Cancel'),
        ('complete', 'Complete'),
        ('reschedule', 'Reschedule'),
        ('reject', 'Reject'),
        ('approve', 'Approve'),
    ]
    
    ITEM_TYPE_CHOICES = [
        ('service', 'Service'),
        ('product', 'Product'),
        ('package', 'Package'),
        ('appointment', 'Appointment'),
        ('cancellation_request', 'Cancellation Request'),
        ('reschedule_request', 'Reschedule Request'),
    ]
    
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    item_id = models.IntegerField()
    item_name = models.CharField(max_length=255)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='history_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True, help_text="Additional details about the action")
    
    class Meta:
        db_table = 'history_logs'
        ordering = ['-timestamp']
        verbose_name = 'History Log'
        verbose_name_plural = 'History Logs'
    
    def __str__(self):
        return f"{self.get_action_type_display()} {self.get_item_type_display()} - {self.item_name} by {self.performed_by.get_full_name() if self.performed_by else 'System'}"


class Treatment(models.Model):
    """Model for storing treatment details when appointments are completed"""
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='treatment')
    treatment_date = models.DateField()
    treatment_time = models.TimeField()
    notes = models.TextField(blank=True, null=True, help_text="Treatment notes and observations")
    next_appointment_recommended = models.DateField(blank=True, null=True, help_text="Recommended date for next appointment")
    products_used = models.TextField(blank=True, null=True, help_text="Products used during treatment")
    duration_minutes = models.IntegerField(blank=True, null=True, help_text="Actual treatment duration in minutes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'treatments'
        ordering = ['-treatment_date', '-treatment_time']
        verbose_name = 'Treatment'
        verbose_name_plural = 'Treatments'
    
    def __str__(self):
        return f"Treatment for {self.appointment.patient.get_full_name()} - {self.treatment_date}"


class TimeSlot(models.Model):
    """Model for managing available appointment time slots"""
    time = models.TimeField(unique=True, help_text="Available appointment time slot")
    is_active = models.BooleanField(default=True, help_text="Whether this time slot is available for booking")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'time_slots'
        ordering = ['time']
        verbose_name = 'Time Slot'
        verbose_name_plural = 'Time Slots'
    
    def __str__(self):
        return f"{self.time.strftime('%I:%M %p')} - {'Active' if self.is_active else 'Inactive'}"


class SMSReminder(models.Model):
    """Model for tracking SMS reminders sent to patients"""
    REMINDER_TYPE_CHOICES = [
        ('one_day', 'One Day Before'),
        ('two_day', 'Two Days Before'),
        ('custom', 'Custom'),
    ]
    
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='sms_reminders')
    reminder_type = models.CharField(max_length=15, choices=REMINDER_TYPE_CHOICES, default='two_day')
    sent = models.BooleanField(default=False, help_text="Whether the reminder SMS has been sent")
    sent_at = models.DateTimeField(blank=True, null=True, help_text="When the SMS reminder was sent")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sms_reminders'
        ordering = ['-created_at']
        unique_together = ['appointment', 'reminder_type']  # One reminder type per appointment
        verbose_name = 'SMS Reminder'
        verbose_name_plural = 'SMS Reminders'
    
    def __str__(self):
        return f"SMS Reminder {self.get_reminder_type_display()} for {self.appointment.patient.get_full_name()}"