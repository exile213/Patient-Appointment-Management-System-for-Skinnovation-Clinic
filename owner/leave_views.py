"""
Owner views for managing attendant leave requests.
When owner approves leave, automatically creates AttendantUnavailabilityRequest 
for all existing appointments on that date and sends SMS to patients with 3-option flow.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
from accounts.models import AttendantLeaveRequest, AttendantProfile
from appointments.models import Appointment, AttendantUnavailabilityRequest, Notification, SMSHistory
from services.utils import send_appointment_sms
from services.template_service import template_service
import logging

logger = logging.getLogger(__name__)


def is_owner(user):
    """Check if user is owner or admin (staff)"""
    return user.is_authenticated and user.user_type in ('owner', 'admin')


@login_required
@user_passes_test(is_owner)
def list_leave_requests(request):
    """List all attendant leave requests with filtering"""
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    attendant_filter = request.GET.get('attendant', '')
    
    # Start with all leave requests
    leave_requests = AttendantLeaveRequest.objects.select_related(
        'attendant_profile__user',
        'reviewed_by'
    ).order_by('-leave_date')
    
    # Apply filters
    if status_filter:
        leave_requests = leave_requests.filter(status=status_filter)
    
    if attendant_filter:
        try:
            attendant_profile = AttendantProfile.objects.get(id=attendant_filter)
            leave_requests = leave_requests.filter(attendant_profile=attendant_profile)
        except AttendantProfile.DoesNotExist:
            pass
    
    # Get statistics
    pending_count = AttendantLeaveRequest.objects.filter(status='pending').count()
    approved_count = AttendantLeaveRequest.objects.filter(status='approved').count()
    rejected_count = AttendantLeaveRequest.objects.filter(status='rejected').count()
    
    # Get all attendants for filter dropdown
    all_attendants = AttendantProfile.objects.select_related('user').all().order_by('user__first_name', 'user__last_name')
    
    # Add pagination
    paginator = Paginator(leave_requests, 20)  # 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'leave_requests': page_obj,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'attendant_filter': attendant_filter,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'all_attendants': all_attendants,
    }
    
    return render(request, 'owner/leave_requests.html', context)


@login_required
@user_passes_test(is_owner)
def approve_leave_request(request, leave_request_id):
    """
    Approve a leave request and trigger unavailability flow for all affected appointments.
    
    When approved:
    1. Mark leave request as approved
    2. Find all appointments for that attendant on that date
    3. Create AttendantUnavailabilityRequest for each appointment with pending_reassignment_choice=True
    4. Send SMS to patients using template_service with portal link
    5. Create notification for patient with special warning badge
    """
    leave_request = get_object_or_404(AttendantLeaveRequest, id=leave_request_id)
    
    if leave_request.status != 'pending':
        messages.error(request, f'Can only approve pending requests. This request is {leave_request.get_status_display()}.')
        return redirect('owner:list_leave_requests')
    
    try:
        # Mark leave request as approved
        leave_request.status = 'approved'
        leave_request.reviewed_by = request.user
        leave_request.reviewed_at = timezone.now()
        leave_request.save()
        
        # Get all appointments for this attendant on the leave date (including pending, scheduled, confirmed, and approved)
        affected_appointments = Appointment.objects.filter(
            attendant=leave_request.attendant_profile.user,
            appointment_date=leave_request.leave_date,
            status__in=['scheduled', 'confirmed', 'pending', 'approved']
        )
        
        affected_count = 0
        
        # For each affected appointment, create unavailability request and notify patient
        for appointment in affected_appointments:
            # Create AttendantUnavailabilityRequest with pending_reassignment_choice=True
            unavailability_request = AttendantUnavailabilityRequest.objects.create(
                appointment=appointment,
                reason=leave_request.reason,
                status='pending',
                pending_reassignment_choice=True  # Patient needs to make a selection
            )
            
            # Create notification for patient with special type for unavailability
            Notification.objects.create(
                type='system',
                title='⚠️ Attendant Unavailable - Action Required',
                message=f"Your attendant is unavailable for your appointment on {leave_request.leave_date.strftime('%B %d, %Y')} at {appointment.appointment_time.strftime('%I:%M %p')}. "
                        f"Please choose: Keep slot with new attendant, Reschedule with same attendant, or Cancel.",
                patient=appointment.patient,
                appointment_id=appointment.id,
                is_read=False
            )
            
            # Send SMS to patient using template_service
            try:
                # Call send_attendant_reassignment from template_service with request context
                result = template_service.send_attendant_reassignment(
                    appointment=appointment,
                    previous_attendant=appointment.attendant,
                    request=request
                )
                
                if result.get('success'):
                    affected_count += 1
                    logger.info(f"Sent unavailability SMS to patient {appointment.patient.id} for appointment {appointment.id}")
                else:
                    logger.error(f"Failed to send SMS to patient {appointment.patient.id}: {result.get('error')}")
            except Exception as e:
                logger.error(f"Exception sending SMS to patient {appointment.patient.id}: {str(e)}")
                # Continue anyway - SMS failure shouldn't block the approval
        
        # Create notification for owner/staff with summary
        Notification.objects.create(
            type='system',
            title='Leave Request Approved',
            message=f"Leave request for {leave_request.attendant_profile.user.get_full_name()} on {leave_request.leave_date} has been approved. "
                    f"{affected_count} patients have been notified and need to make their choice.",
        )
        
        messages.success(
            request,
            f'Leave request approved! {affected_count} affected patient(s) have been notified with 3 options.'
        )
        
    except Exception as e:
        logger.error(f"Error approving leave request {leave_request_id}: {str(e)}")
        messages.error(request, f'Error approving leave request: {str(e)}')
        return redirect('owner:list_leave_requests')
    
    return redirect('owner:leave_request_detail', leave_request_id=leave_request_id)


@login_required
@user_passes_test(is_owner)
def reject_leave_request(request, leave_request_id):
    """Reject a leave request with optional reason"""
    leave_request = get_object_or_404(AttendantLeaveRequest, id=leave_request_id)
    
    if leave_request.status != 'pending':
        messages.error(request, f'Can only reject pending requests. This request is {leave_request.get_status_display()}.')
        return redirect('owner:list_leave_requests')
    
    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        
        try:
            leave_request.status = 'rejected'
            leave_request.reviewed_by = request.user
            leave_request.reviewed_at = timezone.now()
            leave_request.rejection_reason = rejection_reason
            leave_request.save()
            
            # Create notification for attendant
            Notification.objects.create(
                type='system',
                title='Leave Request Rejected',
                message=f"Your leave request for {leave_request.leave_date} has been rejected. "
                        f"Reason: {rejection_reason or 'Not specified'}",
                patient=leave_request.attendant_profile.user
            )
            
            messages.success(request, 'Leave request has been rejected. Attendant has been notified.')
            return redirect('owner:list_leave_requests')
        
        except Exception as e:
            logger.error(f"Error rejecting leave request {leave_request_id}: {str(e)}")
            messages.error(request, f'Error rejecting leave request: {str(e)}')
    
    context = {
        'leave_request': leave_request,
    }
    
    return render(request, 'owner/reject_leave_request.html', context)


@login_required
@user_passes_test(is_owner)
def leave_request_detail(request, leave_request_id):
    """View detailed leave request information"""
    leave_request = get_object_or_404(AttendantLeaveRequest, id=leave_request_id)
    
    # Get affected appointments if approved
    affected_appointments = []
    unavailability_requests = []
    
    if leave_request.status == 'approved':
        affected_appointments = Appointment.objects.filter(
            attendant=leave_request.attendant_profile.user,
            appointment_date=leave_request.leave_date,
            status__in=['scheduled', 'confirmed', 'pending', 'approved']
        )
        
        unavailability_requests = AttendantUnavailabilityRequest.objects.filter(
            appointment__in=affected_appointments
        ).select_related('appointment__patient', 'appointment__service', 'appointment__package', 'appointment__product')
    
    context = {
        'leave_request': leave_request,
        'affected_appointments': affected_appointments,
        'unavailability_requests': unavailability_requests,
    }
    
    return render(request, 'owner/leave_request_detail.html', context)
