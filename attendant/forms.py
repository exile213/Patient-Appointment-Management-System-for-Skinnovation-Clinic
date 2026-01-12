from django import forms
from appointments.models import Diagnosis


class DiagnosisForm(forms.ModelForm):
    class Meta:
        model = Diagnosis
        fields = [
            'blood_pressure',
            'skin_type',
            'lesion_type',
            'target_area',
            'keloid_risk',
            'accutane_history',
            'prescription',
            'follow_up_recommended',
            'notes',
        ]
        widgets = {
            'blood_pressure': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '120/80'}),
            'skin_type': forms.Select(attrs={'class': 'form-select'}),
            'lesion_type': forms.Select(attrs={'class': 'form-select'}),
            'target_area': forms.Select(attrs={'class': 'form-select'}),
            'keloid_risk': forms.Select(attrs={'class': 'form-select'}),
            'accutane_history': forms.Select(attrs={'class': 'form-select'}),
            'prescription': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter prescription or instructions...'}),
            'follow_up_recommended': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'Enter diagnosis notes...'}),
        }
