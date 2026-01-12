from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.management import call_command
from io import StringIO
import sys

@csrf_exempt
@require_http_methods(["GET", "POST"])
def trigger_appointment_reminders(request):
    """
    API endpoint for external cron service (cron-job.org) to trigger appointment reminders.
    
    Security: Requires CRON_SECRET_TOKEN in Authorization header or token query parameter.
    
    Usage:
        GET/POST https://your-app.onrender.com/api/cron/reminders/?filter=2days&token=YOUR_SECRET
        
    Parameters:
        - filter: Required. One of: 2days, 1day, 1hour
        - token: Required. Secret token for authentication (can be in header or query param)
    
    Returns:
        JSON response with execution status and output
    """
    
    # Get secret token from settings
    expected_token = getattr(settings, 'CRON_SECRET_TOKEN', None)
    
    if not expected_token:
        return JsonResponse({
            'success': False,
            'error': 'Cron authentication not configured on server'
        }, status=500)
    
    # Check authentication - accept token from header or query parameter
    provided_token = None
    
    # Check Authorization header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        provided_token = auth_header.replace('Bearer ', '').strip()
    
    # Fallback to query parameter
    if not provided_token:
        provided_token = request.GET.get('token') or request.POST.get('token')
    
    if not provided_token or provided_token != expected_token:
        return JsonResponse({
            'success': False,
            'error': 'Unauthorized: Invalid or missing token'
        }, status=401)
    
    # Get filter parameter
    filter_type = request.GET.get('filter') or request.POST.get('filter')
    
    if not filter_type:
        return JsonResponse({
            'success': False,
            'error': 'Missing required parameter: filter (2days, 1day, or 1hour)'
        }, status=400)
    
    if filter_type not in ['2days', '1day', '1hour']:
        return JsonResponse({
            'success': False,
            'error': f'Invalid filter: {filter_type}. Must be one of: 2days, 1day, 1hour'
        }, status=400)
    
    # Execute management command and capture output
    try:
        output = StringIO()
        call_command('send_appointment_reminders', f'--filter={filter_type}', stdout=output)
        command_output = output.getvalue()
        
        return JsonResponse({
            'success': True,
            'filter': filter_type,
            'message': f'Reminder task executed successfully for filter: {filter_type}',
            'output': command_output
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Command execution failed: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def cron_health_check(request):
    """
    Simple health check endpoint for cron monitoring.
    No authentication required - used to verify the service is running.
    
    Usage:
        GET https://your-app.onrender.com/api/cron/health/
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'Skinovation Beauty Clinic Cron Service',
        'endpoints': {
            'reminders': '/api/cron/reminders/?filter=<2days|1day|1hour>&token=<secret>',
            'health': '/api/cron/health/'
        }
    }, status=200)


@csrf_exempt
@require_http_methods(["GET"])
def cron_debug_appointments(request):
    """
    Debug endpoint to check what appointments would be found for reminders.
    No authentication required - for debugging only.
    
    Usage:
        GET https://your-app.onrender.com/api/cron/debug-appointments/?filter=1hour
    """
    from django.utils import timezone
    from datetime import timedelta, datetime
    from appointments.models import Appointment
    
    filter_type = request.GET.get('filter', '1hour')
    now = timezone.now()
    
    debug_info = {
        'current_time': now.isoformat(),
        'filter': filter_type,
        'appointments_found': [],
        'total_count': 0
    }
    
    if filter_type == '1hour':
        # Get all appointments for today
        appointments = Appointment.objects.filter(
            appointment_date=now.date(),
            status__in=['confirmed', 'scheduled']
        )
        
        debug_info['total_today'] = appointments.count()
        
        # Check each appointment
        for apt in appointments:
            appointment_datetime = timezone.make_aware(
                datetime.combine(apt.appointment_date, apt.appointment_time)
            )
            time_diff = (appointment_datetime - now).total_seconds() / 60
            
            apt_info = {
                'id': apt.id,
                'patient': apt.patient.get_full_name() if apt.patient else 'Unknown',
                'phone': apt.patient.phone if apt.patient else None,
                'appointment_time': apt.appointment_time.isoformat(),
                'appointment_datetime': appointment_datetime.isoformat(),
                'time_diff_minutes': round(time_diff, 1),
                'in_window': 55 <= time_diff <= 65,
                'status': apt.status
            }
            
            debug_info['appointments_found'].append(apt_info)
            
            if 55 <= time_diff <= 65:
                debug_info['total_count'] += 1
    
    return JsonResponse(debug_info, status=200)