from django import forms
from django.core.exceptions import ValidationError
from .models import Package, PackageService
from services.models import Service


class PackageForm(forms.ModelForm):
    """Form for creating and editing packages"""
    
    class Meta:
        model = Package
        fields = ['package_name', 'description', 'price', 'sessions', 'duration_days']
        widgets = {
            'package_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Package name (e.g., 3 + 1 Diamond Peel)',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Package description (optional)',
                'rows': 3
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Price',
                'step': '0.01',
                'required': True
            }),
            'sessions': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of sessions (patient visits)',
                'required': True,
                'min': '1'
            }),
            'duration_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Duration in days',
                'required': True,
                'min': '1'
            }),
            # grace_period_days intentionally omitted until enforcement is implemented
        }

    def clean_package_name(self):
        """Validate package name is not empty"""
        package_name = self.cleaned_data.get('package_name', '').strip()
        if not package_name:
            raise ValidationError('Package name is required.')
        return package_name

    def clean_price(self):
        """Validate price is positive"""
        price = self.cleaned_data.get('price')
        if price and price <= 0:
            raise ValidationError('Price must be greater than 0.')
        return price

    def clean_sessions(self):
        """Validate sessions is positive"""
        sessions = self.cleaned_data.get('sessions')
        if sessions and sessions <= 0:
            raise ValidationError('Sessions must be at least 1.')
        return sessions

    def clean_duration_days(self):
        """Validate duration is positive"""
        duration = self.cleaned_data.get('duration_days')
        if duration and duration <= 0:
            raise ValidationError('Duration must be at least 1 day.')
        return duration

    # No grace_period_days validation for now (field not in form)


class PackageServiceForm(forms.ModelForm):
    """Form for adding services to packages"""
    
    service = forms.ModelChoiceField(
        queryset=Service.objects.filter(archived=False),
        widget=forms.Select(attrs={
            'class': 'form-control service-select',
            'required': True
        }),
        label='Service'
    )

    class Meta:
        model = PackageService
        fields = ['service']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show non-archived services
        self.fields['service'].queryset = Service.objects.filter(archived=False).order_by('service_name')
