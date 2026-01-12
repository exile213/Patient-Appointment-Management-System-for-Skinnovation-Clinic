from django import forms
from appointments.models import Diagnosis


class DiagnosisForm(forms.ModelForm):
    class Meta:
        model = Diagnosis
        fields = ['notes', 'prescription', 'follow_up_recommended']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'Enter diagnosis notes...'}),
            'prescription': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter prescription or instructions...'}),
            'follow_up_recommended': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
