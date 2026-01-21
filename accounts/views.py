from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView, PasswordResetDoneView, PasswordResetCompleteView
from django.urls import reverse, reverse_lazy
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from utils.email import send_mailjet_email
from django.template.loader import render_to_string
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from .models import User
from .forms import CustomUserCreationForm, CustomPasswordResetForm, CustomSetPasswordForm
from .email_service import MailtrapEmailService


def login_selection(request):
    """Main login selection page - Only accessible to staff, attendant, and owner"""
    if request.user.is_authenticated:
        return redirect_to_dashboard(request.user)
    
    # Restrict access - patients should not be able to access this page
    # This page is only for staff (admin), attendant, and owner
    # Patients should use the direct patient login URL
    return render(request, 'accounts/login_selection.html')


@never_cache
@csrf_protect
def patient_login(request):
    """Patient login view - Email-based authentication"""
    if request.user.is_authenticated:
        return redirect_to_dashboard(request.user)
    
    if request.method == 'POST':
        email = request.POST.get('email', '').lower().strip()
        password = request.POST.get('password', '')
        
        if email and password:
            try:
                # Find user by email (case-insensitive)
                user = User.objects.get(email__iexact=email, user_type='patient')
                
                # Check password
                if user.check_password(password) and user.is_active:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.first_name}!')
                    response = redirect('accounts:profile')
                    # Prevent caching of login page
                    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response['Pragma'] = 'no-cache'
                    response['Expires'] = '0'
                    return response
                else:
                    if not user.is_active:
                        messages.error(request, 'Your account is inactive. Please contact support.')
                    else:
                        messages.error(request, 'Invalid email or password.')
            except User.DoesNotExist:
                messages.error(request, 'Invalid email or password.')
            except User.MultipleObjectsReturned:
                messages.error(request, 'Multiple accounts found. Please contact support.')
        else:
            messages.error(request, 'Please enter both email and password.')
    
    response = render(request, 'accounts/patient_login.html')
    # Prevent caching of login page
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@never_cache
@csrf_protect
def admin_login(request):
    """Staff login view - Email-based authentication"""
    if request.user.is_authenticated:
        return redirect_to_dashboard(request.user)
    
    if request.method == 'POST':
        email = request.POST.get('email', '').lower().strip()
        password = request.POST.get('password', '')
        
        if email and password:
            try:
                # Find user by email (case-insensitive)
                user = User.objects.get(email__iexact=email, user_type='admin')
                
                # Check password
                if user.check_password(password) and user.is_active:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.first_name}!')
                    response = redirect('appointments:admin_dashboard')
                    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response['Pragma'] = 'no-cache'
                    response['Expires'] = '0'
                    return response
                else:
                    if not user.is_active:
                        messages.error(request, 'Your account is inactive. Please contact the owner.')
                    else:
                        messages.error(request, 'Invalid email or password.')
            except User.DoesNotExist:
                messages.error(request, 'Invalid email or password.')
            except User.MultipleObjectsReturned:
                messages.error(request, 'Multiple accounts found. Please contact the owner.')
        else:
            messages.error(request, 'Please enter both email and password.')
    
    response = render(request, 'accounts/admin_login.html')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@never_cache
@csrf_protect
def owner_login(request):
    """Owner login view - Email-based authentication"""
    if request.user.is_authenticated:
        return redirect_to_dashboard(request.user)
    
    # Get the next URL from query parameters
    next_url = request.GET.get('next', None)
    
    if request.method == 'POST':
        email = request.POST.get('email', '').lower().strip()
        password = request.POST.get('password', '')
        
        if email and password:
            try:
                # Find user by email (case-insensitive)
                user = User.objects.get(email__iexact=email, user_type='owner')
                
                # Check password
                if user.check_password(password) and user.is_active:
                    login(request, user)
                    messages.success(request, 'Welcome back to Skinnovation Beauty Clinic!')
                    # Redirect to next URL if provided, otherwise to owner dashboard
                    if next_url:
                        response = redirect(next_url)
                    else:
                        response = redirect('owner:dashboard')
                    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response['Pragma'] = 'no-cache'
                    response['Expires'] = '0'
                    return response
                else:
                    if not user.is_active:
                        messages.error(request, 'Your account is inactive.')
                    else:
                        messages.error(request, 'Invalid email or password.')
            except User.DoesNotExist:
                messages.error(request, 'Invalid email or password.')
            except User.MultipleObjectsReturned:
                messages.error(request, 'Multiple accounts found.')
        else:
            messages.error(request, 'Please enter both email and password.')
    
    context = {'next': next_url} if next_url else {}
    response = render(request, 'accounts/owner_login.html', context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@never_cache
@csrf_protect
def attendant_login(request):
    """Attendant login view - Email-based authentication"""
    if request.user.is_authenticated:
        return redirect_to_dashboard(request.user)
    
    # Get the next URL from query parameters
    next_url = request.GET.get('next', None)
    
    if request.method == 'POST':
        email = request.POST.get('email', '').lower().strip()
        password = request.POST.get('password', '')
        
        if email and password:
            try:
                # Find user by email (case-insensitive)
                user = User.objects.get(email__iexact=email, user_type='attendant')
                
                # Check password
                if user.check_password(password) and user.is_active:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.first_name}!')
                    # Redirect to next URL if provided, otherwise to attendant dashboard
                    if next_url:
                        response = redirect(next_url)
                    else:
                        response = redirect('attendant:dashboard')
                    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response['Pragma'] = 'no-cache'
                    response['Expires'] = '0'
                    return response
                else:
                    if not user.is_active:
                        messages.error(request, 'Your account is inactive. Please contact the owner.')
                    else:
                        messages.error(request, 'Invalid email or password.')
            except User.DoesNotExist:
                messages.error(request, 'Invalid email or password.')
            except User.MultipleObjectsReturned:
                messages.error(request, 'Multiple accounts found. Please contact the owner.')
        else:
            messages.error(request, 'Please enter both email and password.')
    
    context = {'next': next_url} if next_url else {}
    response = render(request, 'accounts/attendant_login.html', context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def redirect_to_dashboard(user):
    """Helper function to redirect users to their appropriate dashboard"""
    if user.user_type == 'admin':
        return redirect('appointments:admin_dashboard')
    elif user.user_type == 'owner':
        return redirect('owner:dashboard')
    elif user.user_type == 'attendant':
        return redirect('attendant:dashboard')
    else:
        return redirect('accounts:profile')


def login_view(request):
    """Legacy login view - redirects to selection page"""
    return redirect('accounts:login_selection')


@never_cache
@csrf_protect
def register_view(request):
    """Registration view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    # Get next URL from query parameter
    next_url = request.GET.get('next', '')
    
    # Helper function to get safe redirect URL
    def get_redirect_url():
        from django.utils.http import url_has_allowed_host_and_scheme
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=request.get_host()):
            return next_url
        return 'accounts:profile'
    
    if request.method == 'POST':
        # Get next URL from POST data if available, otherwise from GET
        next_url = request.POST.get('next', request.GET.get('next', ''))
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Send welcome email
            email_sent = False
            try:
                email_service = MailtrapEmailService()
                email_result = email_service.send_welcome_email(user)
                if email_result.get('success'):
                    email_sent = True
                    print(f"Welcome email sent successfully to {user.email}")
                else:
                    print(f"Welcome email failed: {email_result.get('message')}")
            except Exception as e:
                print(f"Exception during welcome email: {str(e)}")
                import traceback
                traceback.print_exc()
            
            # Send welcome SMS
            sms_sent = False
            try:
                if user.phone:
                    from services.utils import send_sms_notification
                    welcome_message = f"Welcome to Skinnovation Beauty Clinic! Hi {user.first_name}, thank you for registering. Browse our services and book your first appointment now!"
                    sms_result = send_sms_notification(user.phone, welcome_message)
                    if sms_result and sms_result.get('success'):
                        sms_sent = True
                        print(f"Welcome SMS sent successfully to {user.phone}")
                    else:
                        print(f"Welcome SMS failed: {sms_result}")
            except Exception as e:
                print(f"Exception during welcome SMS: {str(e)}")
                import traceback
                traceback.print_exc()
            
            # Auto-login the user after registration
            # Authenticate the user to set the backend attribute properly
            # This is required when multiple authentication backends are configured
            authenticated_user = authenticate(
                request,
                username=user.username,
                password=form.cleaned_data['password1']
            )
            if authenticated_user:
                login(request, authenticated_user)
                messages.success(request, f'Account created successfully! Welcome, {user.first_name}!')
                # Redirect to next URL if provided, otherwise to profile
                redirect_target = get_redirect_url()
                response = redirect(redirect_target)
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response
            else:
                # Fallback: manually set backend and login
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                
                # Notify owner of new patient registration
                if user.user_type == 'patient':
                    from appointments.models import Notification
                    from accounts.models import User as UserModel
                    owner_users = UserModel.objects.filter(user_type='owner', is_active=True)
                    for owner in owner_users:
                        Notification.objects.create(
                            type='system',
                            title='New Patient Registered',
                            message=f'New patient {user.get_full_name()} ({user.email}) has registered.',
                            patient=None  # Owner notification
                        )
                
                messages.success(request, f'Account created successfully! Welcome, {user.first_name}!')
                # Redirect to next URL if provided, otherwise to profile
                redirect_target = get_redirect_url()
                response = redirect(redirect_target)
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response
        else:
            messages.error(request, 'Please correct the errors below.')
            # Preserve next_url even when form has errors
            next_url = request.POST.get('next', request.GET.get('next', ''))
    else:
        form = CustomUserCreationForm()
        next_url = request.GET.get('next', '')
    
    # Pass next_url to template so it can be preserved in form
    response = render(request, 'accounts/register.html', {'form': form, 'next_url': next_url})
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@login_required
def profile_view(request):
    """User profile view"""
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
def edit_profile(request):
    """Edit user profile - available for patient and attendant"""
    if request.user.user_type not in ['patient', 'attendant']:
        messages.error(request, 'You do not have permission to edit your profile.')
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        from .forms import ProfileEditForm
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        from .forms import ProfileEditForm
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
@require_http_methods(["POST"])
def verify_password(request):
    """Verify if the entered password is correct for the current user"""
    try:
        data = json.loads(request.body)
        password = data.get('password', '')
        
        if not password:
            return JsonResponse({'valid': False, 'message': 'Password is required'}, status=400)
        
        # Check if password is correct
        if request.user.check_password(password):
            return JsonResponse({'valid': True, 'message': 'Password is correct'})
        else:
            return JsonResponse({'valid': False, 'message': 'Password is incorrect'})
    except json.JSONDecodeError:
        return JsonResponse({'valid': False, 'message': 'Invalid request'}, status=400)
    except Exception as e:
        return JsonResponse({'valid': False, 'message': 'An error occurred'}, status=500)


def test_mailtrap(request):
    """Test view to verify Mailtrap integration"""
    if request.method == 'POST':
        email = request.POST.get('email', 'ksreyes.chmsu@gmail.com')
        name = request.POST.get('name', 'Test User')
        
        email_service = MailtrapEmailService()
        result = email_service.send_test_email(email, name)
        
        if result['success']:
            messages.success(request, f"Test email sent successfully to {email}!")
        else:
            messages.error(request, f"Failed to send test email: {result['message']}")
    
    return render(request, 'accounts/test_mailtrap.html')


# Password Reset Views
class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view for patients"""
    template_name = 'accounts/password_reset.html'
    form_class = CustomPasswordResetForm
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_type'] = 'patient'
        return context
    
    def form_valid(self, form):
        """Override to only send reset emails to patients using Django's email system"""
        email = form.cleaned_data['email']
        try:
            user = User.objects.filter(email=email, user_type='patient').first()
            if user and user.is_active:
                # Generate token and create reset URL
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Create reset URL
                reset_url = self.request.build_absolute_uri(
                    reverse('accounts:password_reset_confirm', kwargs={
                        'uidb64': uid,
                        'token': token
                    })
                )
                
                # Send email using Django's email system
                subject = 'Password Reset - Skinovation Beauty Clinic'
                message = render_to_string('accounts/password_reset_email.html', {
                    'user': user,
                    'reset_url': reset_url,
                    'site_name': 'Skinovation Beauty Clinic',
                })
                
                try:
                    send_mailjet_email(
                        subject,
                        user.email,
                        'accounts/password_reset_email.html',
                        {
                            'user': user,
                            'reset_url': reset_url,
                            'site_name': 'Skinovation Beauty Clinic',
                        }
                    )
                    messages.success(self.request, 'Password reset email sent! Please check your inbox.')
                except Exception as e:
                    messages.error(self.request, f"Failed to send email: {str(e)}")
            else:
                messages.error(self.request, 'No patient account found with this email address or account is inactive.')
        except Exception as e:
            messages.error(self.request, f'An error occurred: {str(e)}')
        
        return redirect(self.success_url)


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Custom password reset confirm view"""
    template_name = 'accounts/password_reset_confirm.html'
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('accounts:password_reset_complete')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_type'] = 'patient'
        return context


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """Custom password reset done view"""
    template_name = 'accounts/password_reset_done.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_type'] = 'patient'
        return context


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """Custom password reset complete view"""
    template_name = 'accounts/password_reset_complete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_type'] = 'patient'
        return context


@login_required
def medical_history(request):
    """Patient view and upload medical history"""
    if request.user.user_type != 'patient':
        messages.error(request, 'This page is only available for patients.')
        return redirect('home')
    
    from .models import MedicalHistory
    
    if request.method == 'POST':
        document_type = request.POST.get('document_type')
        title = request.POST.get('title')
        file = request.FILES.get('file')
        notes = request.POST.get('notes', '')
        
        if document_type and title and file:
            medical_history = MedicalHistory.objects.create(
                patient=request.user,
                document_type=document_type,
                title=title,
                file=file,
                notes=notes
            )
            messages.success(request, 'Medical history document uploaded successfully!')
            return redirect('accounts:medical_history')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    medical_history_list = MedicalHistory.objects.filter(patient=request.user).order_by('-uploaded_at')
    
    context = {
        'medical_history_list': medical_history_list,
    }
    
    return render(request, 'accounts/medical_history.html', context)


@login_required
def delete_medical_history(request, history_id):
    """Delete medical history document"""
    from .models import MedicalHistory
    
    medical_history = get_object_or_404(MedicalHistory, id=history_id, patient=request.user)
    
    if request.method == 'POST':
        medical_history.file.delete()  # Delete the file
        medical_history.delete()  # Delete the record
        messages.success(request, 'Medical history document deleted successfully!')
    
    return redirect('accounts:medical_history')


# Login view logic
from django.shortcuts import render
from django.contrib.auth import authenticate, login

def login_patient(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # Redirect to home after login
        else:
            return render(request, 'accounts/login.html', {'error': 'Invalid credentials'})
    return render(request, 'accounts/login.html')