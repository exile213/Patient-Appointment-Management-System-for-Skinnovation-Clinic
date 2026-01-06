from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    """Form for creating/editing products"""
    
    class Meta:
        model = Product
        fields = ['product_name', 'description', 'price', 'stock', 'product_image']
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'product_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
