from django import forms
from .models import Service, ServiceCategory


class ServiceForm(forms.ModelForm):
    """Form for creating/editing services"""
    
    class Meta:
        model = Service
        fields = ['service_name', 'description', 'price', 'duration', 'category', 'image']
        widgets = {
            'service_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
