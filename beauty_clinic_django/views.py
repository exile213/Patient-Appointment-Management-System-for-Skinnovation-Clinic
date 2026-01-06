from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse


def home(request):
    """Home page view"""
    # Redirect admin users to admin dashboard
    if request.user.is_authenticated and request.user.user_type == 'admin':
        return redirect('appointments:admin_dashboard')
    
    context = {}
    
    # If user is authenticated, fetch appointments within 2 days for pre-appointment confirmation
    if request.user.is_authenticated and request.user.user_type == 'patient':
        from datetime import timedelta
        from django.utils import timezone
        from appointments.models import Appointment
        
        # Get appointments 2 days from now
        reminder_date = timezone.now().date() + timedelta(days=2)
        upcoming_appointments = Appointment.objects.filter(
            patient=request.user,
            appointment_date=reminder_date,
            status__in=['confirmed', 'scheduled']
        ).first()
        
        if upcoming_appointments:
            context['upcoming_appointment'] = upcoming_appointments
    
    response = render(request, 'home.html', context)
    # Prevent caching of home page for logged-out users
    if not request.user.is_authenticated:
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
    return response


@never_cache
@require_http_methods(["GET", "POST"])
def logout_view(request):
    """Logout view with proper cache control to prevent back button access"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    response = redirect('home')
    # Clear all session data
    request.session.flush()
    # Prevent caching of logout page and redirect
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response
