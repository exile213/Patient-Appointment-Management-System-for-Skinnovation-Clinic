from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User
import re


class EmailAuthenticationForm(AuthenticationForm):
    """Custom authentication form using email instead of username"""
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address',
            'autocomplete': 'email',
            'autofocus': True
        }),
        label='Email Address'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'current-password'
        })
    )
    
    def clean_username(self):
        """Validate email and get user by email"""
        email = self.cleaned_data.get('username', '').lower().strip()
        try:
            # Find user by email (case-insensitive)
            user = User.objects.get(email__iexact=email)
            self.user_cache = user
            return email
        except User.DoesNotExist:
            raise ValidationError('No account found with this email address.')
        except User.MultipleObjectsReturned:
            raise ValidationError('Multiple accounts found. Please contact support.')
    
    def clean(self):
        """Override to authenticate with email"""
        username = self.cleaned_data.get('username', '')
        password = self.cleaned_data.get('password', '')
        
        if username and password:
            # Authenticate using email
            from django.contrib.auth import authenticate
            self.user_cache = authenticate(
                request=self.request,
                username=username,
                password=password
            )
            
            if self.user_cache is None:
                raise ValidationError('Invalid email or password.')
            else:
                self.confirm_login_allowed(self.user_cache)
        
        return self.cleaned_data


class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form for our custom User model"""
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'First Name',
            'style': 'text-transform: capitalize;'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Last Name',
            'style': 'text-transform: capitalize;'
        })
    )
    middle_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Middle Name (Optional)'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    phone = forms.CharField(
        max_length=11,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '09123456789',
            'maxlength': '11',
            'pattern': '09[0-9]{9}',
            'title': 'Enter 11-digit Philippine phone number starting with 09'
        })
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'middle_name', 'email', 'phone', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})
    
    def clean_first_name(self):
        """Validate first name - no numbers or symbols"""
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            # Only allow letters, spaces, hyphens, and apostrophes
            if not re.match(r"^[a-zA-Z\s'-]+$", first_name):
                raise ValidationError('First name can only contain letters, spaces, hyphens, and apostrophes.')
        return first_name
    
    def clean_last_name(self):
        """Validate last name - no numbers or symbols"""
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            # Only allow letters, spaces, hyphens, and apostrophes
            if not re.match(r"^[a-zA-Z\s'-]+$", last_name):
                raise ValidationError('Last name can only contain letters, spaces, hyphens, and apostrophes.')
        return last_name
    
    def clean_middle_name(self):
        """Validate middle name - no numbers or symbols"""
        middle_name = self.cleaned_data.get('middle_name')
        if middle_name:
            # Only allow letters, spaces, hyphens, and apostrophes
            if not re.match(r"^[a-zA-Z\s'-]+$", middle_name):
                raise ValidationError('Middle name can only contain letters, spaces, hyphens, and apostrophes.')
        return middle_name
    
    def clean_email(self):
        """Validate email - Google emails only and no duplicates"""
        email = self.cleaned_data.get('email')
        if email:
            # Check if it's a Gmail address
            if not re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', email, re.IGNORECASE):
                raise ValidationError('Please use a valid Gmail address (e.g., yourname@gmail.com)')
            
            # Check for duplicate emails
            if User.objects.filter(email__iexact=email).exists():
                raise ValidationError('This email address is already registered. Please use a different email.')
        
        return email
    
    def clean_phone(self):
        """Validate Philippine phone number format"""
        phone = self.cleaned_data.get('phone')
        
        if not phone:
            raise ValidationError('Phone number is required.')
        
        # Remove any non-digit characters
        phone_digits = re.sub(r'\D', '', phone)
        
        # Check if it's exactly 11 digits and starts with 09
        if len(phone_digits) != 11 or not phone_digits.startswith('09'):
            raise ValidationError(
                'Please enter a valid 11-digit Philippine phone number starting with 09 (e.g., 09123456789)'
            )
        
        return phone_digits  # Return cleaned phone number
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.middle_name = self.cleaned_data['middle_name']
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        user.user_type = 'patient'  # Default to patient
        
        # Auto-generate username from email (part before @)
        email = self.cleaned_data['email']
        base_username = email.split('@')[0].lower()
        username = base_username
        counter = 1
        # Ensure username is unique
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        user.username = username
        
        if commit:
            user.save()
        return user


class CustomPasswordResetForm(PasswordResetForm):
    """Custom password reset form with enhanced styling"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        })


class CustomSetPasswordForm(SetPasswordForm):
    """Custom set password form with enhanced styling"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter new password',
            'autocomplete': 'new-password'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password'
        })


class ProfileEditForm(forms.ModelForm):
    """Form for editing user profile"""
    
    current_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter current password',
            'id': 'id_current_password'
        }),
        help_text='Enter your current password to view it or change it'
    )
    
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password (optional)',
            'id': 'id_new_password'
        }),
        help_text='Leave blank if you don\'t want to change your password'
    )
    
    confirm_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
            'id': 'id_confirm_password'
        })
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'middle_name', 'email', 'phone', 'address', 
                  'gender', 'civil_status', 'birthday', 'age', 'occupation', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'maxlength': '11',
                'pattern': '09[0-9]{9}',
                'inputmode': 'numeric',
                'oninput': 'this.value = this.value.replace(/[^0-9]/g, "").slice(0, 11); if (this.value.length > 0 && !this.value.startsWith("09")) { this.value = "09" + this.value.replace(/^09/, ""); }'
            }),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'civil_status': forms.Select(attrs={'class': 'form-control'}),
            'birthday': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make password fields optional
        self.fields['current_password'].required = False
        self.fields['new_password'].required = False
        self.fields['confirm_password'].required = False
    
    def clean_phone(self):
        """Validate Philippine phone number format"""
        phone = self.cleaned_data.get('phone')
        
        if phone:
            phone_digits = re.sub(r'\D', '', phone)
            if len(phone_digits) != 11 or not phone_digits.startswith('09'):
                raise ValidationError(
                    'Please enter a valid 11-digit Philippine phone number starting with 09 (e.g., 09123456789)'
                )
            return phone_digits
        
        return phone
    
    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get('current_password')
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        # If any password field is filled, validate password change
        if current_password or new_password or confirm_password:
            if not current_password:
                raise ValidationError({
                    'current_password': 'Please enter your current password to change it.'
                })
            
            # Verify current password
            if not self.instance.check_password(current_password):
                raise ValidationError({
                    'current_password': 'Current password is incorrect.'
                })
            
            # If new password is provided, validate it
            if new_password:
                if len(new_password) < 8:
                    raise ValidationError({
                        'new_password': 'Password must be at least 8 characters long.'
                    })
                
                if new_password != confirm_password:
                    raise ValidationError({
                        'confirm_password': 'New passwords do not match.'
                    })
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password')
        
        # If a new password is provided, set it
        if new_password:
            user.set_password(new_password)
        
        if commit:
            user.save()
        return user
