from django import forms
from .models import SMSTemplate, CancellationRequest

class SMSTemplateForm(forms.ModelForm):
    """Form for creating and editing SMS templates"""
    
    class Meta:
        model = SMSTemplate
        fields = ['name', 'template_type', 'subject', 'message', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter template name'
            }),
            'template_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional subject line'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Enter your message template. Use variables like {patient_name}, {appointment_date}, etc.'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add help text for template types
        self.fields['template_type'].help_text = 'Select the type of template for better organization'
        self.fields['message'].help_text = 'Use variables like {patient_name}, {appointment_date}, {appointment_time}, {service_name}, etc.'
        
        # Make subject optional
        self.fields['subject'].required = False
