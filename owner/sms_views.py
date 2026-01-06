from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from services.utils import send_sms_notification
from accounts.models import User
from appointments.models import SMSHistory

def is_owner(user):
    """Check if user is owner or admin (staff)"""
    return user.is_authenticated and user.user_type in ('owner', 'admin')

@login_required
@user_passes_test(is_owner)
def sms_test(request):
    """SMS testing page for owner"""
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        message = request.POST.get('message')
        
        if phone_number and message:
            result = send_sms_notification(phone_number, message, user=request.user)
            
            if result['success']:
                messages.success(request, 'SMS sent successfully!')
            else:
                messages.error(request, f'SMS failed: {result.get("message", "Unknown error")}')
        else:
            messages.error(request, 'Please fill in all fields.')
        
        return redirect('owner:sms_test')
    
    # Get recent patients for quick testing
    recent_patients = User.objects.filter(
        user_type='patient',
        phone__isnull=False
    ).exclude(phone='')[:10]
    
    # Get SMS history for the current user
    sms_history = SMSHistory.objects.filter(sender=request.user)[:20]
    
    context = {
        'recent_patients': recent_patients,
        'sms_history': sms_history,
    }
    
    return render(request, 'owner/sms_test.html', context)

@login_required
@user_passes_test(is_owner)
def send_test_sms(request):
    """AJAX endpoint to send test SMS"""
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        message = request.POST.get('message')
        
        if phone_number and message:
            result = send_sms_notification(phone_number, message, user=request.user)
            return JsonResponse(result)
        else:
            return JsonResponse({
                'success': False,
                'message': 'Phone number and message are required'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })
