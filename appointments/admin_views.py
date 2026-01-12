from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from django.db.models import Q, Sum, Count, Max
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import transaction
from .models import Appointment, Notification, ClosedDay
from accounts.models import User, AttendantProfile
from services.models import Service, ServiceImage, HistoryLog
from products.models import Product, ProductImage
from services.utils import send_appointment_sms

def is_admin(user):
    """Check if user is staff/admin"""
    return user.is_authenticated and user.user_type == 'admin'


def is_admin_or_owner(user):
    """Check if user is admin or owner"""
    return user.is_authenticated and user.user_type in ['admin', 'owner']

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Staff dashboard - shows appointments, orders, and patient list"""
    # Get today's date
    today = timezone.now().date()
    
    # Get all appointments (services and packages) - ordered by most recently created
    all_appointments = (
        Appointment.objects.filter(
            Q(service__isnull=False) | Q(package__isnull=False)
        )
        .select_related('patient', 'service', 'package')
        .order_by('-created_at')[:10]
    )
    
    # Get orders (product appointments) - ordered by most recently created
    pre_orders = (
        Appointment.objects.filter(product__isnull=False)
        .select_related('patient', 'product')
        .order_by('-created_at')[:10]
    )
    
    # Get patient list
    patients = User.objects.filter(user_type='patient').order_by('-date_joined')[:10]
    
    # Get statistics
    total_appointments = Appointment.objects.filter(
        Q(service__isnull=False) | Q(package__isnull=False)
    ).count()
    scheduled_count = Appointment.objects.filter(
        status='scheduled',
        product__isnull=True
    ).count()
    confirmed_count = Appointment.objects.filter(
        status='confirmed',
        product__isnull=True
    ).count()
    no_show_count = Appointment.objects.filter(status='no_show').count()
    pre_order_count = Appointment.objects.filter(product__isnull=False).count()
    total_patients = User.objects.filter(user_type='patient').count()
    
    context = {
        'all_appointments': all_appointments,
        'pre_orders': pre_orders,
        'patients': patients,
        'total_appointments': total_appointments,
        'scheduled_count': scheduled_count,
        'confirmed_count': confirmed_count,
        'no_show_count': no_show_count,
        'pre_order_count': pre_order_count,
        'total_patients': total_patients,
        'today': today,
    }
    
    return render(request, 'appointments/admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_appointments(request):
    """Admin view for all appointments"""
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    search_query = request.GET.get('search', '')
    
    # Calculate statistics BEFORE applying filters (for summary cards)
    total_appointments = Appointment.objects.all().count()
    scheduled_count = Appointment.objects.filter(status='scheduled').count()
    confirmed_count = Appointment.objects.filter(status='confirmed').count()
    cancelled_count = Appointment.objects.filter(status='cancelled').count()
    
    # Start with all appointments - latest bookings first (by creation time, then appointment date/time)
    appointments = (
        Appointment.objects.all()
        .select_related('patient', 'attendant', 'service', 'product', 'package')
        .prefetch_related('feedback')
        .order_by('-created_at', '-appointment_date', '-appointment_time')
    )
    
    # Apply filters
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    if date_filter:
        appointments = appointments.filter(appointment_date=date_filter)
    
    if search_query:
        appointments = appointments.filter(
            Q(patient__first_name__icontains=search_query) |
            Q(patient__last_name__icontains=search_query) |
            Q(service__service_name__icontains=search_query) |
            Q(product__product_name__icontains=search_query) |
            Q(package__package_name__icontains=search_query)
        )
    
    # Add pagination
    paginator = Paginator(appointments, 20)  # 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'appointments': page_obj,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'search_query': search_query,
        'total_appointments': total_appointments,
        'scheduled_count': scheduled_count,
        'confirmed_count': confirmed_count,
        'cancelled_count': cancelled_count,
    }
    
    return render(request, 'appointments/admin_appointments.html', context)

@login_required
@user_passes_test(is_admin)
def admin_appointment_detail(request, appointment_id):
    """Admin view for appointment details"""
    appointment = get_object_or_404(
        Appointment.objects.select_related(
            'patient', 'attendant', 'service', 'product', 'package', 'service__category'
        ),
        id=appointment_id,
    )
    
    # Get attendants - get all active attendant users
    attendants = User.objects.filter(user_type='attendant', is_active=True).order_by('first_name', 'last_name')
    
    context = {
        'appointment': appointment,
        'attendants': attendants,
    }
    
    return render(request, 'appointments/admin_appointment_detail.html', context)


@login_required
@user_passes_test(is_admin)
def admin_mark_attendant_unavailable(request, appointment_id):
    """Mark attendant as unavailable - triggers patient 3-option flow"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        
        if not reason:
            messages.error(request, 'Please provide a reason for unavailability.')
            return redirect('appointments:admin_appointment_detail', appointment_id=appointment_id)
        
        # Create unavailability request
        from .models import AttendantUnavailabilityRequest
        unavailability_request = AttendantUnavailabilityRequest.objects.create(
            appointment=appointment,
            reason=reason,
            status='pending'
        )
        
        # Create notification for patient with 3 options
        Notification.objects.create(
            type='appointment',
            appointment_id=appointment.id,
            title='Attendant Unavailable - Please Choose an Option',
            message=f'Your assigned attendant {appointment.attendant.first_name} {appointment.attendant.last_name} is unavailable for your appointment on {appointment.appointment_date} at {appointment.appointment_time}. Reason: {reason}. Please choose one of the following options: 1) Choose another attendant, 2) Reschedule with same attendant, or 3) Cancel appointment.',
            patient=appointment.patient
        )
        
        # Send SMS notification
        sms_result = send_appointment_sms(
            appointment,
            'unavailable',
            reason=reason,
            unavailability_request_id=unavailability_request.id
        )
        
        messages.success(request, f'Patient has been notified. They will receive options to choose another attendant, reschedule, or cancel.')
        return redirect('appointments:admin_appointment_detail', appointment_id=appointment_id)
    
    return redirect('appointments:admin_appointment_detail', appointment_id=appointment_id)


@login_required
@user_passes_test(is_admin)
def admin_send_sms(request, appointment_id):
    """Send SMS to patient from appointment detail page"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('appointments:admin_appointment_detail', appointment_id=appointment_id)
    
    # Get the message from the form
    message = request.POST.get('message', '').strip()
    
    if not message:
        messages.error(request, 'Please provide a message to send.')
        return redirect('appointments:admin_appointment_detail', appointment_id=appointment_id)
    
    # Check if patient has phone number
    if not appointment.patient.phone:
        messages.error(request, 'Patient does not have a phone number. Please update patient profile first.')
        return redirect('appointments:admin_appointment_detail', appointment_id=appointment_id)
    
    # Send SMS using the SMS service
    try:
        from services.sms_service import sms_service
        result = sms_service.send_sms(appointment.patient.phone, message)
        
        if result.get('success'):
            messages.success(request, f'SMS sent successfully to {appointment.patient.get_full_name()} at {appointment.patient.phone}.')
        else:
            error_msg = result.get('error', 'Unknown error')
            messages.error(request, f'Failed to send SMS: {error_msg}')
    except Exception as e:
        messages.error(request, f'Error sending SMS: {str(e)}')
    
    return redirect('appointments:admin_appointment_detail', appointment_id=appointment_id)


@login_required
@user_passes_test(is_admin)
def admin_reassign_attendant(request, appointment_id):
    """Reassign an appointment to a different attendant and notify the patient"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method for reassigning attendants.')
        return redirect('appointments:admin_appointment_detail', appointment_id=appointment_id)
    
    attendant_id = request.POST.get('attendant_id')
    note = request.POST.get('note', '').strip()
    
    if not attendant_id:
        messages.error(request, 'Please select a staff member to assign.')
        return redirect('appointments:admin_appointment_detail', appointment_id=appointment_id)
    
    try:
        new_attendant = User.objects.get(id=attendant_id, user_type='attendant')
    except User.DoesNotExist:
        messages.error(request, 'Selected staff member does not exist.')
        return redirect('appointments:admin_appointment_detail', appointment_id=appointment_id)
    
    previous_attendant = appointment.attendant
    if previous_attendant == new_attendant:
        messages.info(request, f'{new_attendant.first_name} {new_attendant.last_name} is already assigned to this appointment.')
        return redirect('appointments:admin_appointment_detail', appointment_id=appointment_id)
    
    appointment.attendant = new_attendant
    appointment.save()
    
    # Create a notification for the patient
    message_body = (
        f'Your appointment on {appointment.appointment_date} at {appointment.appointment_time} '
        f'will now be handled by {new_attendant.first_name} {new_attendant.last_name}.'
    )
    if note:
        message_body += f' Note from staff: {note}'
    
    Notification.objects.create(
        type='appointment',
        appointment_id=appointment.id,
        title='Appointment Staff Updated',
        message=message_body,
        patient=appointment.patient
    )
    
    # Send SMS notification
    sms_result = send_appointment_sms(
        appointment,
        'reassignment',
        previous_attendant=previous_attendant
    )
    
    if sms_result.get('success'):
        messages.success(
            request,
            f'Appointment reassigned to {new_attendant.first_name} {new_attendant.last_name}. Patient notified via SMS.'
        )
    else:
        error_msg = sms_result.get('error', 'Unknown error')
        if 'phone number not available' in error_msg.lower():
            messages.warning(
                request,
                f'Appointment reassigned to {new_attendant.first_name} {new_attendant.last_name}, but SMS could not be sent: Patient phone number is missing. Please contact patient directly.'
            )
        else:
            messages.warning(
                request,
                f'Appointment reassigned to {new_attendant.first_name} {new_attendant.last_name}, but SMS notification failed: {error_msg}'
            )
    
    return redirect('appointments:admin_appointment_detail', appointment_id=appointment_id)

@login_required
@user_passes_test(is_admin)
def admin_confirm_appointment(request, appointment_id):
    """Admin confirm an appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if appointment.status == 'scheduled':
        appointment.status = 'confirmed'
        appointment.save()
        
        # If this is a product order, deduct stock based on quantity
        if appointment.product:
            product = appointment.product
            quantity = appointment.quantity if hasattr(appointment, 'quantity') and appointment.quantity else 1
            old_stock = product.stock
            
            if product.stock >= quantity:
                product.stock -= quantity
                product.save()
                
                # Log stock reduction
                log_stock_change(
                    product=product,
                    action='order',
                    quantity_change=-quantity,
                    previous_stock=old_stock,
                    new_stock=product.stock,
                    staff=request.user,
                    reason=f"Customer order confirmed - Appointment #{appointment.id} for {appointment.patient.get_full_name()}"
                )
            else:
                messages.warning(request, f'Warning: Stock for {product.product_name} ({product.stock} units) is less than ordered quantity ({quantity}). Stock set to 0.')
                # Log stock reduction to 0
                log_stock_change(
                    product=product,
                    action='order',
                    quantity_change=-old_stock,
                    previous_stock=old_stock,
                    new_stock=0,
                    staff=request.user,
                    reason=f"Customer order confirmed (insufficient stock) - Appointment #{appointment.id} for {appointment.patient.get_full_name()}"
                )
                product.stock = 0
                product.save()
        
        # Get attendant name for notification (if appointment has an attendant)
        attendant_name = None
        if appointment.attendant:
            attendant_name = f"{appointment.attendant.first_name} {appointment.attendant.last_name}"
        
        # Create notification for patient with attendant details
        if appointment.product:
            # Product order notification
            Notification.objects.create(
                type='confirmation',
                appointment_id=appointment.id,
                title='Order Confirmed',
                message=f'Your order for {appointment.get_service_name()} (Claim Date: {appointment.appointment_date} at {appointment.appointment_time.strftime("%I:%M %p")}) has been confirmed.',
                patient=appointment.patient
            )
        else:
            # Service/Package appointment notification
            message = f'Your appointment for {appointment.get_service_name()} on {appointment.appointment_date} at {appointment.appointment_time.strftime("%I:%M %p")} has been confirmed.'
            if attendant_name:
                message += f' Your attendant is {attendant_name}.'
            
            Notification.objects.create(
                type='confirmation',
                appointment_id=appointment.id,
                title='Appointment Confirmed',
                message=message,
                patient=appointment.patient
            )
        
        # Notify staff of appointment confirmation
        Notification.objects.create(
            type='confirmation',
            appointment_id=appointment.id,
            title='Appointment Confirmed',
            message=f'Appointment for {appointment.patient.get_full_name()} - {appointment.get_service_name()} on {appointment.appointment_date} at {appointment.appointment_time} has been confirmed.',
            patient=None  # Staff notification
        )
        
        # Send SMS confirmation to patient with attendant details
        sms_result = send_appointment_sms(appointment, 'confirmation')
        patient_sms_sent = sms_result['success']
        patient_sms_error = sms_result.get('error', '') if not patient_sms_sent else ''
        
        # Send SMS notification to attendant (only for service/package appointments)
        attendant_sms_sent = False
        attendant_notified = False
        if appointment.attendant:  # Only send to attendant if appointment has one
            try:
                attendant_user = User.objects.filter(
                    user_type='attendant',
                    first_name=appointment.attendant.first_name,
                    last_name=appointment.attendant.last_name,
                    is_active=True
                ).first()
                
                if attendant_user:
                    # Send SMS to attendant
                    attendant_sms_result = send_attendant_assignment_sms(appointment)
                    attendant_sms_sent = attendant_sms_result.get('success', False)
                    
                    # Create in-app notification for attendant
                    Notification.objects.create(
                        type='appointment',
                        appointment_id=appointment.id,
                        title='Appointment Confirmed and Assigned',
                        message=f'An appointment has been confirmed and assigned to you. Patient: {appointment.patient.get_full_name()} - {appointment.get_service_name()} on {appointment.appointment_date} at {appointment.appointment_time.strftime("%I:%M %p")}.',
                        patient=attendant_user  # Store attendant user in patient field for notification
                    )
                    attendant_notified = True
            except Exception as e:
                pass
        
        # Consolidated success message
        if patient_sms_sent and attendant_sms_sent:
            messages.success(request, f'Appointment confirmed successfully. Notifications sent to patient and attendant.')
        elif patient_sms_sent:
            messages.success(request, f'Appointment confirmed. Patient notified via SMS.')
        else:
            # Appointment confirmed but SMS had issues
            messages.success(request, f'Appointment confirmed successfully.')
        
        # Log appointment confirmation
        log_appointment_history('confirm', appointment, request.user)
    else:
        messages.error(request, 'Only scheduled appointments can be confirmed.')
    
    return redirect('appointments:admin_appointment_detail', appointment_id=appointment_id)

@login_required
@user_passes_test(is_admin)
def admin_complete_appointment(request, appointment_id):
    """Admin mark appointment as completed"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if appointment.status in ['scheduled', 'confirmed']:
        # Ensure a transaction_id exists for this appointment
        import uuid
        if not appointment.transaction_id:
            appointment.transaction_id = str(uuid.uuid4())[:8].upper()

        appointment.status = 'completed'
        appointment.save()
        
        # Create notification for patient
        Notification.objects.create(
            type='appointment',
            appointment_id=appointment.id,
            title='Appointment Completed',
            message=f'Your appointment for {appointment.get_service_name()} on {appointment.appointment_date} has been completed. Thank you for choosing Skinovation Beauty Clinic!',
            patient=appointment.patient
        )
        
        messages.success(request, f'Appointment for {appointment.patient.full_name} has been marked as completed.')
        
        # Log appointment completion
        log_appointment_history('complete', appointment, request.user)
    else:
        messages.error(request, 'Only scheduled or confirmed appointments can be completed.')
    
    return redirect('appointments:admin_appointment_detail', appointment_id=appointment_id)

@login_required
@user_passes_test(is_admin)
def admin_cancel_appointment(request, appointment_id):
    """Admin cancel an appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, 'Cancellation reason is required.')
            return redirect('appointments:admin_appointment_detail', appointment_id=appointment_id)
    
    if appointment.status in ['scheduled', 'confirmed']:
        # Get reason from POST or set default
        reason = request.POST.get('reason', '').strip() if request.method == 'POST' else 'Cancelled by admin'
        
        appointment.status = 'cancelled'
        appointment.save()
        
        # Create cancellation request record with reason
        from .models import CancellationRequest
        appointment_type = 'package' if appointment.package else 'regular'
        CancellationRequest.objects.create(
            appointment_id=appointment.id,
            appointment_type=appointment_type,
            patient=appointment.patient,
            reason=reason,
            status='approved'  # Auto-approved since admin is cancelling
        )
        
        # Create notification for patient
        Notification.objects.create(
            type='cancellation',
            appointment_id=appointment.id,
            title='Appointment Cancelled',
            message=f'Your appointment for {appointment.get_service_name()} on {appointment.appointment_date} at {appointment.appointment_time} has been cancelled. Please contact us to reschedule.',
            patient=appointment.patient
        )
        
        # Notify owner of appointment cancellation (single notification for all owners)
        Notification.objects.create(
            type='cancellation',
            appointment_id=appointment.id,
            title='Appointment Cancelled',
            message=f'Appointment for {appointment.patient.get_full_name()} - {appointment.get_service_name()} on {appointment.appointment_date} at {appointment.appointment_time} has been cancelled.',
            patient=None  # Owner notification
        )
        
        # Send SMS cancellation notification
        sms_result = send_appointment_sms(appointment, 'cancellation')
        if sms_result['success']:
            messages.success(request, f'Appointment for {appointment.patient.full_name} has been cancelled. SMS sent.')
        else:
            messages.success(request, f'Appointment for {appointment.patient.full_name} has been cancelled. (SMS failed)')
        
        # Log appointment cancellation
        log_appointment_history('cancel', appointment, request.user)
    else:
        messages.error(request, 'Only scheduled or confirmed appointments can be cancelled.')
    
    return redirect('appointments:admin_appointment_detail', appointment_id=appointment_id)

@login_required
@user_passes_test(is_admin)
def admin_delete_appointment(request, appointment_id):
    """Permanently delete an appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Store patient name and service name before deletion
    patient_name = appointment.patient.get_full_name()
    service_name = appointment.get_service_name()
    
    # Delete the appointment
    appointment.delete()
    
    messages.success(request, f'Appointment for {patient_name} - {service_name} has been permanently deleted.')
    return redirect('appointments:admin_appointments')

@login_required
@user_passes_test(is_admin)
def admin_mark_no_show(request, appointment_id):
    """Mark appointment as no-show when patient doesn't arrive"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if appointment.status == 'confirmed':
        appointment.status = 'no_show'
        appointment.save()
        
        # Create notification for patient about no-show
        Notification.objects.create(
            type='no_show',
            appointment_id=appointment.id,
            title='Appointment Marked as No-Show',
            message=f'You did not arrive for your appointment on {appointment.appointment_date} at {appointment.appointment_time} for {appointment.get_service_name()}. Please contact us to reschedule or cancel future appointments if you cannot attend.',
            patient=appointment.patient
        )
        
        # If product order, restore stock since patient didn't show up
        if appointment.product:
            product = appointment.product
            quantity = appointment.quantity if hasattr(appointment, 'quantity') and appointment.quantity else 1
            old_stock = product.stock
            product.stock += quantity
            product.save()
            
            # Log stock restoration
            log_stock_change(
                product=product,
                action='return',
                quantity_change=quantity,
                previous_stock=old_stock,
                new_stock=product.stock,
                staff=request.user,
                reason=f"Stock restored - Patient no-show for appointment #{appointment.id}"
            )
            
            messages.info(request, f'Stock for {product.product_name} has been restored (+{quantity} units).')
        
        messages.success(request, f'Appointment marked as NO-SHOW. Patient {appointment.patient.get_full_name()} did not arrive.')
    else:
        messages.error(request, 'Only confirmed appointments can be marked as no-show.')
    
    return redirect('appointments:admin_appointment_detail', appointment_id=appointment_id)

@login_required
@user_passes_test(is_admin)
def admin_maintenance(request):
    """Admin maintenance page"""
    from services.models import Service, HistoryLog
    from packages.models import Package
    from products.models import Product, StockHistory
    from django.db.models import Q
    from datetime import timedelta
    from django.utils import timezone
    
    # Count only active/non-archived items
    services_count = Service.objects.filter(archived=False).count()
    packages_count = Package.objects.filter(archived=False).count()
    products_count = Product.objects.filter(archived=False).count()
    
    # Combine all activity into a unified list
    activity_list = []
    
    # Get history log entries (manually tracked edits/additions/deletions)
    history_logs = HistoryLog.objects.all().order_by('-datetime')[:20]
    for log in history_logs:
        activity_list.append({
            'created_at': log.datetime,
            'type': log.type.lower(),
            'name': log.name,
            'action': log.action,
            'performed_by': log.performed_by,
            'details': log.details or f'{log.action} {log.type.lower()}'
        })
    
    # Get stock history (product inventory changes)
    stock_changes = StockHistory.objects.select_related('product', 'staff').order_by('-created_at')[:20]
    for stock in stock_changes:
        action_display = dict(StockHistory.ACTION_CHOICES).get(stock.action, stock.action)
        staff_name = stock.staff.get_full_name() if stock.staff else 'System'
        activity_list.append({
            'created_at': stock.created_at,
            'type': 'product',
            'name': stock.product.product_name,
            'action': action_display,
            'performed_by': staff_name,
            'details': f'{action_display}: {abs(stock.quantity)} units (Stock: {stock.previous_stock} → {stock.new_stock})'
        })
    
    # Get recently created services
    recent_services = Service.objects.filter(
        archived=False,
        created_at__gte=timezone.now() - timedelta(days=30)
    ).order_by('-created_at')[:15]
    
    for service in recent_services:
        # Only add creation if not already in history log
        if not any(a['type'] == 'service' and a['name'] == service.service_name and 
                  a['action'] in ['Added', 'Created'] and 
                  abs((a['created_at'] - service.created_at).total_seconds()) < 60 
                  for a in activity_list):
            activity_list.append({
                'created_at': service.created_at,
                'type': 'service',
                'name': service.service_name,
                'action': 'Created',
                'performed_by': 'Staff',
                'details': f'New service added'
            })
    
    # Get recently created packages
    recent_packages = Package.objects.filter(
        archived=False,
        created_at__gte=timezone.now() - timedelta(days=30)
    ).order_by('-created_at')[:15]
    
    for package in recent_packages:
        if not any(a['type'] == 'package' and a['name'] == package.package_name and 
                  a['action'] in ['Added', 'Created'] and 
                  abs((a['created_at'] - package.created_at).total_seconds()) < 60 
                  for a in activity_list):
            activity_list.append({
                'created_at': package.created_at,
                'type': 'package',
                'name': package.package_name,
                'action': 'Created',
                'performed_by': 'Staff',
                'details': f'New package added'
            })
    
    # Get recently created products
    recent_products = Product.objects.filter(
        archived=False,
        created_at__gte=timezone.now() - timedelta(days=30)
    ).order_by('-created_at')[:15]
    
    for product in recent_products:
        if not any(a['type'] == 'product' and a['name'] == product.product_name and 
                  a['action'] in ['Added', 'Created'] and 
                  abs((a['created_at'] - product.created_at).total_seconds()) < 60 
                  for a in activity_list):
            activity_list.append({
                'created_at': product.created_at,
                'type': 'product',
                'name': product.product_name,
                'action': 'Created',
                'performed_by': 'Staff',
                'details': f'New product added'
            })
    
    # Sort by created_at (newest first) and take top 20
    activity_list.sort(key=lambda x: x['created_at'], reverse=True)
    recent_activity = activity_list[:20]
    
    context = {
        'services_count': services_count,
        'packages_count': packages_count,
        'products_count': products_count,
        'recent_activity': recent_activity,
    }
    
    return render(request, 'appointments/admin_maintenance.html', context)


@login_required
@user_passes_test(is_admin)
def admin_backfill_transaction_ids(request):
    """Run backfill of missing transaction_id from the web (POST only)."""
    from django.contrib import messages
    import uuid

    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('appointments:admin_maintenance')

    only_completed = request.POST.get('only_completed') == '1'
    dry_run = request.POST.get('dry_run') == '1'
    # batch size to limit work per request (avoid timeouts/oom)
    try:
        batch_size = int(request.POST.get('batch_size', 50))
    except Exception:
        batch_size = 50
    batch_size = max(1, min(batch_size, 500))

    base_qs = Appointment.objects.filter(transaction_id__isnull=True) | Appointment.objects.filter(transaction_id='')
    base_qs = base_qs.distinct()
    if only_completed:
        base_qs = base_qs.filter(status='completed')

    total_missing = base_qs.count()
    # limit to a batch to keep request time short
    qs = base_qs.order_by('id')[:batch_size]

    assigned = 0
    try:
        for appt in qs.iterator():
            # generate a short unique id; collisions are extremely unlikely
            tid = str(uuid.uuid4())[:8].upper()
            # rare collision check within DB
            tries = 0
            while Appointment.objects.filter(transaction_id=tid).exists() and tries < 5:
                tid = str(uuid.uuid4())[:8].upper()
                tries += 1

            if not dry_run:
                appt.transaction_id = tid
                appt.save(update_fields=['transaction_id'])
            assigned += 1
    except Exception as e:
        messages.error(request, f'Error during backfill: {e}')
        return redirect('appointments:admin_maintenance')

    messages.success(request, f'Backfill processed batch: assigned {assigned} ids (dry_run={dry_run}). Total missing before run: {total_missing}.')
    return redirect('appointments:admin_maintenance')

@login_required
@user_passes_test(is_admin)
def admin_patients(request):
    """Admin patients management page"""
    from accounts.models import User
    
    # Annotate counts in the database to avoid N+1 queries that time out on Render
    patients = (
        User.objects.filter(user_type='patient')
        .annotate(
            total_appointments=Count('appointments', distinct=True),
            completed_appointments=Count(
                'appointments',
                filter=Q(appointments__status='completed'),
                distinct=True,
            ),
            cancelled_appointments=Count(
                'appointments',
                filter=Q(appointments__status='cancelled'),
                distinct=True,
            ),
            packages_count=Count(
                'appointments',
                filter=Q(appointments__package__isnull=False),
                distinct=True,
            ),
            last_visit=Max(
                'appointments__appointment_date',
                filter=Q(appointments__status='completed'),
            ),
        )
        .order_by('-id')
    )

    # Add pagination
    paginator = Paginator(patients, 20)  # 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Map annotated patients to the structure expected by the template
    patient_stats = [
        {
            'patient': patient,
            'total_appointments': patient.total_appointments,
            'completed_appointments': patient.completed_appointments,
            'cancelled_appointments': patient.cancelled_appointments,
            'packages_count': patient.packages_count,
            'last_visit': patient.last_visit,
        }
        for patient in page_obj
    ]
    
    context = {
        'patient_stats': patient_stats,
        'page_obj': page_obj,
        'total_patients': patients.count(),
    }
    
    return render(request, 'appointments/admin_patients.html', context)

@login_required
@user_passes_test(is_admin)
def patient_history(request, patient_id):
    """View patient's appointment history and transaction records"""
    from accounts.models import User
    
    patient = get_object_or_404(User, id=patient_id, user_type='patient')
    
    # Get all appointments for this patient, ordered by most recent first
    appointments = (
        Appointment.objects.filter(patient=patient)
        .select_related('service', 'product', 'package', 'attendant')
        .order_by('-created_at')
    )
    
    # Calculate statistics
    total_appointments = appointments.count()
    completed_count = appointments.filter(status='completed').count()
    confirmed_count = appointments.filter(status='confirmed').count()
    scheduled_count = appointments.filter(status='scheduled').count()
    cancelled_count = appointments.filter(status='cancelled').count()
    
    # Calculate total spent (only completed appointments)
    from decimal import Decimal
    total_spent = Decimal('0.00')
    for appointment in appointments.filter(status='completed'):
        if appointment.service:
            total_spent += appointment.service.price
        elif appointment.package:
            total_spent += appointment.package.price
        elif appointment.product:
            quantity = appointment.quantity if hasattr(appointment, 'quantity') and appointment.quantity else 1
            total_spent += appointment.product.price * quantity
    
    context = {
        'patient': patient,
        'appointments': appointments,
        'total_appointments': total_appointments,
        'completed_count': completed_count,
        'confirmed_count': confirmed_count,
        'scheduled_count': scheduled_count,
        'cancelled_count': cancelled_count,
        'total_spent': total_spent,
    }
    
    return render(request, 'appointments/patient_history.html', context)

@login_required
@user_passes_test(is_admin_or_owner)
def service_history(request):
    """Admin view: list of rendered (completed) service transactions"""
    # Only include appointments that are service (not product/package)
    qs = Appointment.objects.filter(service__isnull=False)

    # Status filter: default to 'completed' for rendered services, 'all' to show all statuses
    status = request.GET.get('status', 'completed')
    if status and status != 'all':
        qs = qs.filter(status=status)

    # Date range filter (YYYY-MM-DD expected from <input type="date">)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        try:
            sd = datetime.strptime(start_date, '%Y-%m-%d').date()
            qs = qs.filter(appointment_date__gte=sd)
        except Exception:
            sd = None
    else:
        sd = None

    if end_date:
        try:
            ed = datetime.strptime(end_date, '%Y-%m-%d').date()
            qs = qs.filter(appointment_date__lte=ed)
        except Exception:
            ed = None
    else:
        ed = None

    qs = qs.select_related('service', 'patient', 'attendant').order_by('-appointment_date', '-appointment_time')

    # Pagination
    page_number = request.GET.get('page')
    paginator = Paginator(qs, 20)  # 20 items per page
    page_obj = paginator.get_page(page_number)

    # Provide status options to template
    status_options = [
        ('all', 'All'),
        ('scheduled', 'Scheduled'),
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('rescheduled', 'Rescheduled'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No-Show'),
        ('approved', 'Approved'),
    ]

    # compute sliding page range (max 5 pages visible)
    current = page_obj.number
    total_pages = paginator.num_pages
    window = 5
    half = window // 2
    start_page = max(1, current - half)
    end_page = min(total_pages, start_page + window - 1)
    # shift start if we are at the end and don't have full window
    if end_page - start_page + 1 < window:
        start_page = max(1, end_page - window + 1)

    page_range_window = list(range(start_page, end_page + 1))

    context = {
        'service_history': page_obj,
        'page_obj': page_obj,
        'start_date': sd,
        'end_date': ed,
        'total_results': paginator.count,
        'status': status,
        'status_options': status_options,
        'page_range_window': page_range_window,
    }

    return render(request, 'appointments/service_history.html', context)


@login_required
@user_passes_test(is_admin_or_owner)
def service_history_detail(request, pk):
    """Admin view: full details for a completed service transaction"""
    item = get_object_or_404(Appointment, pk=pk, status='completed', service__isnull=False)
    return render(request, 'appointments/service_history_detail.html', {'item': item})
@login_required
@user_passes_test(is_admin)
def admin_notifications(request):
    """Admin notifications management page"""
    notifications = Notification.objects.all().order_by('-created_at')
    
    # Add pagination
    paginator = Paginator(notifications, 25)  # 25 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notifications': page_obj,
        'page_obj': page_obj,
    }
    
    return render(request, 'appointments/admin_notifications.html', context)

def get_attendant_display_name(user):
    """Get formatted display name for attendant: 'Attendant X - First Last'"""
    # Extract number from username (e.g., 'attendant1' -> 1)
    import re
    match = re.search(r'attendant(\d+)', user.username.lower())
    if match:
        number = match.group(1)
        name = user.get_full_name() or user.username
        return f"Attendant {number} - {name}"
    # Fallback if username doesn't match pattern
    return user.get_full_name() or user.username


@login_required
@user_passes_test(is_admin)
def admin_seed_diagnoses(request):
    """Preview and seed minimal, realistic Diagnosis records for completed appointments that lack one.

    GET: show preview (count and sample). POST: create diagnoses (batch-limited).
    This view is temporary — remove after use.
    """
    from .models import Diagnosis

    # Query completed appointments that don't have a Diagnosis yet
    qs = Appointment.objects.filter(status='completed', diagnosis__isnull=True).select_related(
        'patient', 'service', 'product', 'package', 'attendant'
    ).order_by('id')

    total = qs.count()
    sample = list(qs[:20])

    if request.method == 'POST':
        # Options: dry run and batch size
        dry_run = request.POST.get('dry_run') == '1'
        try:
            batch_size = int(request.POST.get('batch_size') or 200)
        except Exception:
            batch_size = 200
        batch_size = max(1, min(batch_size, 1000))

        # Deterministic, small curated seed data for realism
        diag_notes = [
            'Mild acneiform eruption; advised topical cleanser and sunscreen.',
            'Superficial pigmentation noted; recommend skin-lightening serum and sunscreen.',
            'Localized wart; plan cryotherapy or topical salicylic acid treatment.',
            'Skin tag observed; discuss removal options and consent.',
            'Comedonal acne predominant; advised extraction and topical retinoid.',
            'Post-inflammatory hyperpigmentation; advised topical regimen and sunscreen.'
        ]
        prescriptions = [
            'Topical cleanser twice daily; sunscreen SPF30+; review in 4 weeks.',
            'Hydroquinone 4% nightly; sunscreen daily; monitor for irritation.',
            'Cryotherapy session recommended; paracetamol PRN for discomfort.',
            'Removal procedure discussed; topical antibiotic if needed post-procedure.',
            'Topical retinoid at night; gentle moisturizer AM/PM.',
            'Azelaic acid 15% twice daily; sunscreen; follow-up in 6 weeks.'
        ]
        skin_types = ['I', 'II', 'III', 'IV', 'V', 'VI']
        lesion_types = ['warts', 'moles', 'skin_tags', 'syringoma', 'milia', 'other']

        created_ids = []
        errors = []

        # Process in a transaction; limit to batch_size to keep request short
        processed = 0
        try:
            with transaction.atomic():
                for appt in qs[:batch_size]:
                    processed += 1
                    try:
                        # Build deterministic index from appointment id
                        idx = appt.id % len(diag_notes)

                        diag_date = appt.appointment_date or timezone.now().date()
                        diag_time = appt.appointment_time or timezone.now().time()

                        # Minimal realistic fields
                        defaults = {
                            'diagnosed_by': request.user,
                            'diagnosis_date': diag_date,
                            'diagnosis_time': diag_time,
                            'notes': diag_notes[idx],
                            'prescription': prescriptions[idx % len(prescriptions)],
                            'skin_type': skin_types[idx % len(skin_types)],
                            'lesion_type': lesion_types[idx % len(lesion_types)],
                        }

                        if dry_run:
                            # Do not persist during dry run
                            continue

                        # Create Diagnosis (OneToOne with Appointment)
                        diag = Diagnosis.objects.create(appointment=appt, **defaults)
                        created_ids.append(diag.id)
                    except Exception as e:
                        errors.append(f'Appointment {appt.id}: {e}')
        except Exception as e:
            messages.error(request, f'Error during seeding: {e}')
            return redirect('appointments:admin_maintenance')

        if dry_run:
            messages.info(request, f'Dry run: {total} appointments found; previewed {min(total, batch_size)} items.')
        else:
            messages.success(request, f'Created {len(created_ids)} diagnoses (processed {processed}).')

        context = {
            'total': total,
            'sample': sample,
            'created_ids': created_ids,
            'errors': errors,
            'dry_run': dry_run,
            'batch_size': batch_size,
        }
        return render(request, 'appointments/seed_diagnoses.html', context)

    # GET - preview
    context = {
        'total': total,
        'sample': sample,
    }
    return render(request, 'appointments/seed_diagnoses.html', context)


@login_required
@user_passes_test(is_admin)
def admin_settings(request):
    """Admin settings page"""
    from .models import ClosedDay, TimeSlot
    from packages.models import Package
    
    closed_days = ClosedDay.objects.all()
    # Get all attendant users for the table (both active and inactive)
    attendant_users = (
        User.objects.filter(user_type='attendant')
        .select_related('attendant_profile')
        .order_by('username')
    )
    # Get only active attendant users for the calendar view
    active_attendant_users = (
        User.objects.filter(user_type='attendant', is_active=True)
        .select_related('attendant_profile')
        .order_by('username')
    )
    
    # Get attendant profiles - create list of tuples for easier template access
    attendant_users_with_profiles = []
    attendant_display_names = {}
    for user in attendant_users:
        try:
            profile = user.attendant_profile
            attendant_users_with_profiles.append((user, profile))
        except AttendantProfile.DoesNotExist:
            attendant_users_with_profiles.append((user, None))
        except Exception as e:
            # Handle any database errors gracefully
            from django.db import OperationalError
            if isinstance(e, OperationalError):
                # If there's a database error, try to continue without profile
                attendant_users_with_profiles.append((user, None))
            else:
                attendant_users_with_profiles.append((user, None))
        # Store display name for template
        attendant_display_names[user.id] = get_attendant_display_name(user)
    
    # Create a list of hours for the schedule (10:00 AM to 5:00 PM only)
    hours = ['10', '11', '12', '13', '14', '15', '16', '17']
    
    # Check if today is a closed day
    today = timezone.now().date()
    is_today_closed = ClosedDay.objects.filter(date=today).exists()
    
    # Get all time slots
    timeslots = TimeSlot.objects.all().order_by('time')
    
    # Get all packages with their configurations
    packages = Package.objects.filter(archived=False).order_by('package_name')
    
    context = {
        'closed_days': closed_days,
        'hours': hours,
        'attendant_users': attendant_users,
        'active_attendant_users': active_attendant_users,
        'attendant_users_with_profiles': attendant_users_with_profiles,
        'attendant_display_names': attendant_display_names,
        'is_today_closed': is_today_closed,
        'today': today,
        'timeslots': timeslots,
        'packages': packages,
    }
    
    return render(request, 'appointments/admin_settings.html', context)

@login_required
@user_passes_test(is_admin)
def admin_add_attendant(request):
    """Add new attendant"""
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        shift_date = request.POST.get('shift_date')
        shift_time = request.POST.get('shift_time')
        
        if first_name and last_name:
            messages.info(request, 'Attendants are now managed as User accounts. Please use the user creation interface.')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    return redirect('appointments:admin_settings')

@login_required
@user_passes_test(is_admin)
def admin_delete_attendant(request, attendant_id):
    """Delete attendant user account"""
    attendant = get_object_or_404(User, id=attendant_id, user_type='attendant')
    attendant_name = f"{attendant.first_name} {attendant.last_name}"
    attendant.delete()
    
    messages.success(request, f'Attendant {attendant_name} deleted successfully.')
    return redirect('appointments:admin_settings')


@login_required
@user_passes_test(is_admin)
def admin_create_attendant_user(request):
    """Create a new attendant user account"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        # Validate required fields (email and phone are now optional)
        if not all([username, password, first_name, last_name]):
            messages.error(request, 'Username, password, first name, and last name are required.')
            return redirect('appointments:admin_settings')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'That username is already taken. Please choose another one.')
            return redirect('appointments:admin_settings')
        
        # Create user
        user = User.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            user_type='attendant',
            is_active=True
        )
        user.set_password(password)
        user.save()
        
        messages.success(request, f'Profile created for {first_name} {last_name}.')
    
    return redirect('appointments:admin_settings')


@login_required
@user_passes_test(is_admin)
def admin_toggle_attendant_user(request, user_id):
    """Activate or deactivate an attendant user account"""
    user = get_object_or_404(User, id=user_id, user_type='attendant')
    user.is_active = not user.is_active
    user.archived = not user.is_active
    user.save()
    
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'Attendant account {user.username} has been {status}.')
    return redirect('appointments:admin_settings')


@login_required
@user_passes_test(is_admin)
def admin_edit_attendant_user(request, user_id):
    """Edit attendant user account"""
    user = get_object_or_404(User, id=user_id, user_type='attendant')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        
        if not all([first_name, last_name, username]):
            messages.error(request, 'First name, last name, and username are required.')
            return redirect('appointments:admin_edit_attendant_user', user_id=user_id)
        
        # Check if username is taken by another user
        if User.objects.filter(username=username).exclude(id=user_id).exists():
            messages.error(request, 'That username is already taken. Please choose another one.')
            return redirect('appointments:admin_edit_attendant_user', user_id=user_id)
        
        # Update user
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.middle_name = middle_name if middle_name else ''
        user.save()
        
        messages.success(request, f'Attendant account {username} has been updated successfully.')
        return redirect('appointments:admin_settings')
    
    return render(request, 'appointments/admin_edit_attendant_user.html', {'attendant_user': user})


@login_required
@user_passes_test(is_admin)
def admin_manage_attendant_profile(request, user_id):
    """Manage attendant profile (work days, hours, phone, and profile picture)"""
    user = get_object_or_404(User, id=user_id, user_type='attendant')
    
    if request.method == 'POST':
        work_days = request.POST.getlist('work_days')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        phone = request.POST.get('phone', '').strip()
        
        if not work_days:
            messages.error(request, 'Please select at least one work day.')
            return redirect('appointments:admin_settings')
        
        if not start_time or not end_time:
            messages.error(request, 'Please provide both start and end times.')
            return redirect('appointments:admin_settings')
        
        # Validate store hours restriction (10 AM - 6 PM)
        from datetime import datetime
        start_time_obj = datetime.strptime(start_time, '%H:%M').time()
        end_time_obj = datetime.strptime(end_time, '%H:%M').time()
        min_time = datetime.strptime('10:00', '%H:%M').time()
        max_time = datetime.strptime('18:00', '%H:%M').time()
        
        if start_time_obj < min_time or end_time_obj > max_time:
            messages.error(request, 'Shift hours must be between 10:00 AM and 6:00 PM.')
            return redirect('appointments:admin_settings')
        
        if start_time_obj >= end_time_obj:
            messages.error(request, 'Start time must be before end time.')
            return redirect('appointments:admin_settings')
        
        # Validate phone number if provided
        if phone:
            import re
            if not re.match(r'^09\d{9}$', phone):
                messages.error(request, 'Phone number must be 11 digits starting with 09 (e.g., 09123456789).')
                return redirect('appointments:admin_settings')
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            profile_picture = request.FILES['profile_picture']
            # Validate file type
            if profile_picture.content_type not in ['image/jpeg', 'image/jpg', 'image/png']:
                messages.error(request, 'Profile picture must be in JPG or PNG format.')
                return redirect('appointments:admin_settings')
            user.profile_picture = profile_picture
            user.save()
        
        # Get or create profile
        profile, created = AttendantProfile.objects.get_or_create(user=user)
        profile.work_days = work_days
        profile.start_time = start_time
        profile.end_time = end_time
        if phone:
            profile.phone = phone
        elif phone == '':
            profile.phone = None
        profile.save()
        
        if created:
            messages.success(request, f'Profile created for {user.get_full_name()}.')
        else:
            messages.success(request, f'Profile updated for {user.get_full_name()}.')
        
        return redirect('appointments:admin_settings')
    
    return redirect('appointments:admin_settings')

@login_required
@user_passes_test(is_admin)
def admin_reset_attendant_password(request, user_id):
    """Reset attendant account password and provide a temporary one"""
    from django.contrib.auth.models import User as DjangoUser
    import secrets
    import string
    
    user = get_object_or_404(User, id=user_id, user_type='attendant')
    
    # Generate a random 10-character password
    chars = string.ascii_letters + string.digits
    temp_password = ''.join(secrets.choice(chars) for _ in range(10))
    
    user.set_password(temp_password)
    user.save()
    
    messages.success(
        request,
        f'Password for {user.username} has been reset. Temporary password: {temp_password}'
    )
    return redirect('appointments:admin_settings')


@login_required
@user_passes_test(is_admin)
def admin_delete_notification(request, notification_id):
    """Delete notification"""
    notification = get_object_or_404(Notification, id=notification_id)
    notification.delete()
    
    messages.success(request, 'Notification deleted successfully.')
    return redirect('appointments:admin_notifications')

@login_required
@user_passes_test(is_admin)
def admin_view_patient(request, patient_id):
    """View patient details"""
    from accounts.models import User
    
    patient = get_object_or_404(User, id=patient_id)
    appointments = (
        Appointment.objects.filter(patient=patient)
        .select_related('service', 'product', 'package', 'attendant')
        .order_by('-appointment_date')
    )
    
    context = {
        'patient': patient,
        'appointments': appointments,
    }
    
    return render(request, 'appointments/admin_patient_detail.html', context)

@login_required
@user_passes_test(is_admin)
def admin_edit_patient(request, patient_id):
    """View patient (Data Privacy - view only, no editing allowed)"""
    from accounts.models import User
    
    patient = get_object_or_404(User, id=patient_id, user_type='patient')
    
    # Data Privacy Act compliance - Staff can only VIEW patient profiles, not edit
    messages.info(request, 'Staff can only view patient profiles. Editing is restricted to comply with Data Privacy Act.')
    
    appointments = (
        Appointment.objects.filter(patient=patient)
        .select_related('service', 'product', 'package', 'attendant')
        .order_by('-appointment_date')
    )
    
    context = {
        'patient': patient,
        'appointments': appointments,
    }
    
    return render(request, 'appointments/admin_patient_detail.html', context)

@login_required
@user_passes_test(is_admin)
def admin_delete_patient(request, patient_id):
    """Delete patient - Access denied (Data Privacy Act compliance)"""
    from accounts.models import User
    
    patient = get_object_or_404(User, id=patient_id)
    
    # Access control: Staff cannot delete patient profiles
    # Access control matrix specifies: Staff can only VIEW patient profiles
    messages.warning(request, f'Access denied: Patient profile deletion is restricted for data privacy compliance. Contact owner for data deletion requests.')
    return redirect('appointments:admin_patients')

@login_required
@user_passes_test(is_admin)
def admin_add_closed_day(request):
    """Add closed day"""
    if request.method == 'POST':
        from .models import ClosedDay
        
        date = request.POST.get('start_date')
        reason = request.POST.get('reason')
        
        if date and reason:
            try:
                closed_day = ClosedDay.objects.create(date=date, reason=reason)
                messages.success(request, f'Closed day {date} added successfully.')
                
                # Log the action
                performed_by_name = request.user.get_full_name() or request.user.username
                HistoryLog.objects.create(
                    type='Closed Day',
                    name=f'{date} Closed Day',
                    action='Added',
                    performed_by=performed_by_name,
                    details=f'Reason: {reason}',
                    related_id=closed_day.id
                )
            except Exception as e:
                messages.error(request, f'Error adding closed day: {str(e)}')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    return redirect('appointments:admin_settings')

@login_required
@user_passes_test(is_admin)
def admin_delete_closed_day(request, closed_day_id):
    """Delete closed day"""
    from .models import ClosedDay
    
    closed_day = get_object_or_404(ClosedDay, id=closed_day_id)
    date_str = str(closed_day.date)
    reason_str = closed_day.reason or 'No reason provided'
    
    # Log the action before deleting
    performed_by_name = request.user.get_full_name() or request.user.username
    HistoryLog.objects.create(
        type='Closed Day',
        name=f'{date_str} Closed Day',
        action='Deleted',
        performed_by=performed_by_name,
        details=f'Reason was: {reason_str}',
        related_id=closed_day_id
    )
    
    closed_day.delete()
    
    messages.success(request, 'Closed day deleted successfully.')
    return redirect('appointments:admin_settings')

@login_required
@user_passes_test(is_admin)
def admin_cancellation_requests(request):
    """Admin view for cancellation and reschedule requests"""
    from .models import CancellationRequest, RescheduleRequest, Appointment
    
    cancellation_requests = CancellationRequest.objects.all().order_by('-created_at')
    reschedule_requests = RescheduleRequest.objects.all().order_by('-created_at')

    # Paginate both lists separately so each table has independent pages
    reschedule_paginator = Paginator(reschedule_requests, 20)  # 20 items per page
    cancellation_paginator = Paginator(cancellation_requests, 20)  # 20 items per page

    reschedule_page_number = request.GET.get('page_reschedule')
    cancellation_page_number = request.GET.get('page_cancel')

    reschedule_page_obj = reschedule_paginator.get_page(reschedule_page_number)
    cancellation_page_obj = cancellation_paginator.get_page(cancellation_page_number)
    
    # Bulk-fetch related appointments to avoid N+1 queries
    res_ids = [req.appointment_id for req in reschedule_page_obj]
    cancel_ids = [req.appointment_id for req in cancellation_page_obj]
    all_ids = list(set(res_ids + cancel_ids))
    appointments_map = {
        a.id: a
        for a in Appointment.objects.filter(id__in=all_ids).select_related(
            'patient', 'service', 'product', 'package'
        )
    }

    # Map appointments to reschedule and cancellation requests
    reschedule_requests_with_appointments = [
        (res_req, appointments_map.get(res_req.appointment_id))
        for res_req in reschedule_page_obj
    ]
    cancellation_requests_with_appointments = [
        (can_req, appointments_map.get(can_req.appointment_id))
        for can_req in cancellation_page_obj
    ]
    
    context = {
        'cancellation_requests': cancellation_page_obj,
        'reschedule_requests': reschedule_page_obj,
        'cancellation_page_obj': cancellation_page_obj,
        'reschedule_page_obj': reschedule_page_obj,
        'reschedule_requests_with_appointments': reschedule_requests_with_appointments,
        'cancellation_requests_with_appointments': cancellation_requests_with_appointments,
    }
    
    return render(request, 'appointments/admin_reschedules_cancellations.html', context)

@login_required
@user_passes_test(is_admin)
def admin_approve_cancellation(request, request_id):
    """Admin approve cancellation request"""
    from .models import CancellationRequest
    
    cancellation_request = get_object_or_404(CancellationRequest, id=request_id)
    appointment = get_object_or_404(Appointment, id=cancellation_request.appointment_id)
    
    if cancellation_request.status == 'pending':
        # Update cancellation request status
        cancellation_request.status = 'approved'
        cancellation_request.save()
        
        # Cancel the appointment
        appointment.status = 'cancelled'
        appointment.save()
        
        # Create notification for patient
        Notification.objects.create(
            type='cancellation',
            appointment_id=appointment.id,
            title='Cancellation Approved',
            message=f'Your cancellation request for {appointment.get_service_name()} on {appointment.appointment_date} at {appointment.appointment_time} has been approved.',
            patient=appointment.patient
        )
        
        messages.success(request, f'Cancellation request approved for {appointment.patient.full_name}.')
        
        # Log cancellation approval
        from .models import HistoryLog
        HistoryLog.objects.create(
            action_type='approve',
            item_type='cancellation_request',
            item_id=cancellation_request.id,
            item_name=f"Cancellation Request #{cancellation_request.id} - {appointment.patient.get_full_name()}",
            performed_by=request.user,
            details={
                'appointment_id': appointment.id,
                'patient': appointment.patient.get_full_name(),
                'reason': cancellation_request.reason or '',
            }
        )
    else:
        messages.error(request, 'This cancellation request has already been processed.')
    
    return redirect('appointments:admin_cancellation_requests')

@login_required
@user_passes_test(is_admin)
def admin_reject_cancellation(request, request_id):
    """Admin reject cancellation request"""
    from .models import CancellationRequest
    
    cancellation_request = get_object_or_404(CancellationRequest, id=request_id)
    appointment = get_object_or_404(Appointment, id=cancellation_request.appointment_id)
    
    if cancellation_request.status == 'pending':
        # Update cancellation request status
        cancellation_request.status = 'rejected'
        cancellation_request.save()
        
        # Create notification for patient
        Notification.objects.create(
            type='cancellation',
            appointment_id=appointment.id,
            title='Cancellation Request Rejected',
            message=f'Your cancellation request for {appointment.get_service_name()} on {appointment.appointment_date} at {appointment.appointment_time} has been rejected. Please contact us for more information.',
            patient=appointment.patient
        )
        
        messages.success(request, f'Cancellation request rejected for {appointment.patient.full_name}.')
        
        # Log cancellation rejection
        from .models import HistoryLog
        HistoryLog.objects.create(
            action_type='reject',
            item_type='cancellation_request',
            item_id=cancellation_request.id,
            item_name=f"Cancellation Request #{cancellation_request.id} - {appointment.patient.get_full_name()}",
            performed_by=request.user,
            details={
                'appointment_id': appointment.id,
                'patient': appointment.patient.get_full_name(),
                'reason': cancellation_request.reason or '',
            }
        )
    else:
        messages.error(request, 'This cancellation request has already been processed.')
    
    return redirect('appointments:admin_cancellation_requests')


@login_required
@user_passes_test(is_admin)
def admin_approve_reschedule(request, request_id):
    """Admin approve reschedule request"""
    from .models import RescheduleRequest
    
    reschedule_request = get_object_or_404(RescheduleRequest, id=request_id)
    appointment = get_object_or_404(Appointment, id=reschedule_request.appointment_id)
    
    if reschedule_request.status == 'pending':
        # Check if the new date is a Sunday (clinic closed)
        if reschedule_request.new_appointment_date.weekday() == 6:  # 6 = Sunday
            messages.error(request, f'Cannot approve reschedule: The clinic is closed on Sundays. Please ask the patient to select a weekday.')
            return redirect('appointments:admin_cancellation_requests')
        
        # Check if the new date is a closed clinic day
        if ClosedDay.objects.filter(date=reschedule_request.new_appointment_date).exists():
            closed_day = ClosedDay.objects.get(date=reschedule_request.new_appointment_date)
            reason_text = f" ({closed_day.reason})" if closed_day.reason else ""
            messages.error(request, f'Cannot approve reschedule: The clinic is closed on {reschedule_request.new_appointment_date.strftime("%B %d, %Y")}{reason_text}.')
            return redirect('appointments:admin_cancellation_requests')
        
        # Validate time is between 10:00 AM and 5:00 PM
        import datetime
        time_obj = reschedule_request.new_appointment_time
        min_time = datetime.time(10, 0)  # 10:00 AM
        max_time = datetime.time(17, 0)  # 5:00 PM
        
        if time_obj < min_time or time_obj > max_time:
            messages.error(request, f'Cannot approve reschedule: Time must be between 10:00 AM and 5:00 PM. Selected time was {time_obj.strftime("%I:%M %p")}.')
            return redirect('appointments:admin_cancellation_requests')
        
        # Update reschedule request status
        reschedule_request.status = 'approved'
        reschedule_request.save()
        
        # Update the appointment with new date and time
        old_date = appointment.appointment_date
        old_time = appointment.appointment_time
        appointment.appointment_date = reschedule_request.new_appointment_date
        appointment.appointment_time = reschedule_request.new_appointment_time
        appointment.status = 'approved'  # Set to approved after reschedule approval
        appointment.save()
        
        # Create notification for patient
        Notification.objects.create(
            type='reschedule',
            appointment_id=appointment.id,
            title='Reschedule Request Approved',
            message=f'Your reschedule request for {appointment.get_service_name()} has been approved. New date and time: {reschedule_request.new_appointment_date} at {reschedule_request.new_appointment_time}.',
            patient=appointment.patient
        )
        
        messages.success(request, f'Reschedule request approved for {appointment.patient.full_name}.')
        
        # Log reschedule approval
        log_appointment_history('reschedule', appointment, request.user, {
            'old_date': str(old_date),
            'old_time': str(old_time),
            'new_date': str(reschedule_request.new_appointment_date),
            'new_time': str(reschedule_request.new_appointment_time),
            'reschedule_request_id': reschedule_request.id,
        })
    else:
        messages.error(request, 'This reschedule request has already been processed.')
    
    return redirect('appointments:admin_cancellation_requests')


@login_required
@user_passes_test(is_admin)
def admin_reject_reschedule(request, request_id):
    """Admin reject reschedule request"""
    from .models import RescheduleRequest
    
    reschedule_request = get_object_or_404(RescheduleRequest, id=request_id)
    appointment = get_object_or_404(Appointment, id=reschedule_request.appointment_id)
    
    if reschedule_request.status == 'pending':
        # Update reschedule request status
        reschedule_request.status = 'rejected'
        reschedule_request.save()
        
        # Create notification for patient
        Notification.objects.create(
            type='reschedule',
            appointment_id=appointment.id,
            title='Reschedule Request Rejected',
            message=f'Your reschedule request for {appointment.get_service_name()} on {appointment.appointment_date} at {appointment.appointment_time} has been rejected. Please contact us for more information.',
            patient=appointment.patient
        )
        
        messages.success(request, f'Reschedule request rejected for {appointment.patient.full_name}.')
        
        # Log reschedule rejection
        from .models import HistoryLog
        HistoryLog.objects.create(
            action_type='reject',
            item_type='reschedule_request',
            item_id=reschedule_request.id,
            item_name=f"Reschedule Request #{reschedule_request.id} - {appointment.patient.get_full_name()}",
            performed_by=request.user,
            details={
                'appointment_id': appointment.id,
                'patient': appointment.patient.get_full_name(),
                'requested_date': str(reschedule_request.new_appointment_date),
                'requested_time': str(reschedule_request.new_appointment_time),
            }
        )
    else:
        messages.error(request, 'This reschedule request has already been processed.')
    
    return redirect('appointments:admin_cancellation_requests')


@login_required
@user_passes_test(is_admin)
def admin_manage_service_images(request):
    """Admin view to manage service images"""
    # Only show active (non-archived) services
    all_services = Service.objects.filter(archived=False).prefetch_related('images').order_by('service_name')
    
    if request.method == 'POST':
        service_id = request.POST.get('service_id')
        if service_id:
            service = get_object_or_404(Service, id=service_id)
            # Handle image upload
            if 'image' in request.FILES:
                image = request.FILES['image']
                alt_text = request.POST.get('alt_text', '')
                is_primary = request.POST.get('is_primary') == 'on'
                
                # If this is set as primary, unset other primary images for this service
                if is_primary:
                    ServiceImage.objects.filter(service=service, is_primary=True).update(is_primary=False)
                
                ServiceImage.objects.create(
                    service=service,
                    image=image,
                    alt_text=alt_text,
                    is_primary=is_primary
                )
                messages.success(request, f'Image uploaded successfully for {service.service_name}')
            else:
                messages.error(request, 'Please select an image to upload')
    
    # Add pagination
    paginator = Paginator(all_services, 15)  # 15 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'services': page_obj,
        'page_obj': page_obj,
        'all_services': all_services,  # Pass all services for dropdown
    }
    return render(request, 'appointments/admin_manage_service_images.html', context)


@login_required
@user_passes_test(is_admin)
def admin_manage_product_images(request):
    """Admin view to manage product images"""
    # Only show active (non-archived) products
    products = Product.objects.filter(archived=False).prefetch_related('images').order_by('product_name')
    
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        if product_id:
            product = get_object_or_404(Product, id=product_id)
            # Handle image upload
            if 'image' in request.FILES:
                image = request.FILES['image']
                alt_text = request.POST.get('alt_text', '')
                is_primary = request.POST.get('is_primary') == 'on'
                
                # If this is set as primary, unset other primary images for this product
                if is_primary:
                    ProductImage.objects.filter(product=product, is_primary=True).update(is_primary=False)
                
                ProductImage.objects.create(
                    product=product,
                    image=image,
                    alt_text=alt_text,
                    is_primary=is_primary
                )
                messages.success(request, f'Image uploaded successfully for {product.product_name}')
            else:
                messages.error(request, 'Please select an image to upload')
    
    # Add pagination
    paginator = Paginator(products, 15)  # 15 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'page_obj': page_obj,
    }
    return render(request, 'appointments/admin_manage_product_images.html', context)


@login_required
@user_passes_test(is_admin)
def admin_delete_service_image(request, image_id):
    """Delete a service image"""
    image = get_object_or_404(ServiceImage, id=image_id)
    service_name = image.service.service_name
    image.delete()
    messages.success(request, f'Image deleted successfully for {service_name}')
    return redirect('appointments:admin_manage_service_images')


@login_required
@user_passes_test(is_admin)
def admin_delete_all_service_images(request, service_id):
    """Delete all images for a specific service"""
    service = get_object_or_404(Service, id=service_id)
    image_count = service.images.count()
    
    if image_count > 0:
        service.images.all().delete()
        messages.success(request, f'All {image_count} image(s) deleted successfully for {service.service_name}')
    else:
        messages.info(request, f'No images to delete for {service.service_name}')
    
    return redirect('appointments:admin_manage_service_images')


@login_required
@user_passes_test(is_admin)
def admin_keep_one_image_per_service(request):
    """Keep only one image per service (preferably primary, or first one)"""
    services_updated = 0
    total_deleted = 0
    
    for service in Service.objects.all():
        images = service.images.all()
        image_count = images.count()
        
        if image_count > 1:
            # Try to find primary image first
            primary_image = images.filter(is_primary=True).first()
            
            if primary_image:
                # Keep primary, delete the rest
                images.exclude(id=primary_image.id).delete()
                deleted_count = image_count - 1
            else:
                # No primary, keep the first one (oldest)
                first_image = images.order_by('id').first()
                if first_image:
                    images.exclude(id=first_image.id).delete()
                    deleted_count = image_count - 1
                else:
                    deleted_count = 0
            
            if deleted_count > 0:
                services_updated += 1
                total_deleted += deleted_count
    
    if services_updated > 0:
        messages.success(request, f'Updated {services_updated} service(s). Deleted {total_deleted} duplicate image(s). Each service now has only 1 image.')
    else:
        messages.info(request, 'No services needed updating. All services already have 1 or fewer images.')
    
    return redirect('appointments:admin_manage_service_images')


@login_required
@user_passes_test(is_admin)
def admin_delete_product_image(request, image_id):
    """Delete a product image"""
    image = get_object_or_404(ProductImage, id=image_id)
    product_name = image.product.product_name
    image.delete()
    messages.success(request, f'Image deleted successfully for {product_name}')
    return redirect('appointments:admin_manage_product_images')


@login_required
@user_passes_test(is_admin)
def admin_set_primary_service_image(request, image_id):
    """Set a service image as primary"""
    image = get_object_or_404(ServiceImage, id=image_id)
    # Unset other primary images for this service
    ServiceImage.objects.filter(service=image.service, is_primary=True).update(is_primary=False)
    # Set this image as primary
    image.is_primary = True
    image.save()
    messages.success(request, f'Primary image updated for {image.service.service_name}')
    return redirect('appointments:admin_manage_service_images')


@login_required
@user_passes_test(is_admin)
def admin_set_primary_product_image(request, image_id):
    """Set a product image as primary"""
    image = get_object_or_404(ProductImage, id=image_id)
    # Unset other primary images for this product
    ProductImage.objects.filter(product=image.product, is_primary=True).update(is_primary=False)
    # Set this image as primary
    image.is_primary = True
    image.save()
    messages.success(request, f'Primary image updated for {image.product.product_name}')
    return redirect('appointments:admin_manage_product_images')


@login_required
@user_passes_test(is_admin)
def admin_view_feedback(request):
    """Staff view patient feedback - Only shows service/package/product ratings, not attendant ratings (private)"""
    from .models import Feedback
    
    # Get all feedback, but exclude attendant_rating in display (Data Privacy - attendant feedback is private)
    feedbacks = Feedback.objects.all().order_by('-created_at')
    
    # Add pagination
    from django.core.paginator import Paginator
    paginator = Paginator(feedbacks, 20)  # 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'feedbacks': page_obj,
        'page_obj': page_obj,
    }
    
    return render(request, 'appointments/admin_feedback.html', context)


@login_required
@user_passes_test(is_admin)
def admin_inventory(request):
    """Staff inventory management for products"""
    from products.models import StockHistory
    
    # Only show active (non-archived) products
    products = Product.objects.filter(archived=False).order_by('product_name')
    
    # Get low stock products (stock < 10) - only active products
    low_stock_products = products.filter(stock__lt=10)
    
    # Get out of stock products - only active products
    out_of_stock_products = products.filter(stock=0)
    
    # Get recent stock history (paginated)
    recent_stock_history_qs = StockHistory.objects.select_related('product', 'staff').order_by('-created_at')
    stock_history_paginator = Paginator(recent_stock_history_qs, 20)  # 20 items per page
    stock_history_page_number = request.GET.get('page_stock')
    stock_history_page_obj = stock_history_paginator.get_page(stock_history_page_number)
    
    # Statistics
    total_products = products.count()
    total_stock_value = sum(p.price * p.stock for p in products)
    low_stock_count = low_stock_products.count()
    out_of_stock_count = out_of_stock_products.count()
    
    context = {
        'products': products,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'recent_stock_history': stock_history_page_obj,
        'stock_history_page_obj': stock_history_page_obj,
        'total_products': total_products,
        'total_stock_value': total_stock_value,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
    }
    
    return render(request, 'appointments/admin_inventory.html', context)


def log_appointment_history(action_type, appointment, performed_by, details=None):
    """Helper function to log appointment history"""
    from .models import HistoryLog
    
    # Get appointment name
    if appointment.service:
        item_name = f"{appointment.service.service_name} - {appointment.patient.get_full_name()}"
    elif appointment.product:
        item_name = f"{appointment.product.product_name} - {appointment.patient.get_full_name()}"
    elif appointment.package:
        item_name = f"{appointment.package.package_name} - {appointment.patient.get_full_name()}"
    else:
        item_name = f"Appointment #{appointment.id} - {appointment.patient.get_full_name()}"
    
    # Prepare details
    log_details = {
        'appointment_id': appointment.id,
        'patient': appointment.patient.get_full_name(),
        'date': str(appointment.appointment_date),
        'time': str(appointment.appointment_time),
        'status': appointment.status,
    }
    if details:
        log_details.update(details)
    
    HistoryLog.objects.create(
        action_type=action_type,
        item_type='appointment',
        item_id=appointment.id,
        item_name=item_name,
        performed_by=performed_by,
        details=log_details
    )


def log_stock_change(product, action, quantity_change, previous_stock, new_stock, staff, reason=""):
    """Helper function to log stock changes to inventory history"""
    from products.models import StockHistory
    
    StockHistory.objects.create(
        product=product,
        action=action,
        quantity=quantity_change,
        previous_stock=previous_stock,
        new_stock=new_stock,
        reason=reason,
        staff=staff
    )


@login_required
@user_passes_test(is_admin)
def admin_history_log(request):
    """Admin view for history log with filtering"""
    from services.models import HistoryLog
    from django.db.models import Q
    from accounts.models import User
    
    # Get filter parameters
    patient_filter = request.GET.get('patient', '')
    treatment_filter = request.GET.get('treatment', '')
    attendant_filter = request.GET.get('attendant', '')
    year_filter = request.GET.get('year', '')
    type_filter = request.GET.get('type', '')
    
    history_logs = HistoryLog.objects.all()
    
    # Filter by patient (search in details or performed_by)
    if patient_filter:
        history_logs = history_logs.filter(
            Q(details__icontains=patient_filter) |
            Q(performed_by__icontains=patient_filter)
        )
    
    # Filter by treatment/service (search in name or details)
    if treatment_filter:
        history_logs = history_logs.filter(
            Q(name__icontains=treatment_filter) |
            Q(details__icontains=treatment_filter)
        )
    
    # Filter by attendant (search in details or performed_by)
    if attendant_filter:
        history_logs = history_logs.filter(
            Q(details__icontains=attendant_filter) |
            Q(performed_by__icontains=attendant_filter)
        )
    
    # Filter by year
    if year_filter:
        history_logs = history_logs.filter(datetime__year=year_filter)
    
    # Filter by type (Service, Product, Package)
    if type_filter:
        history_logs = history_logs.filter(type=type_filter)
    
    history_logs = history_logs.order_by('-datetime')
    
    # Get unique years for filter dropdown
    years = HistoryLog.objects.dates('datetime', 'year', order='DESC').values_list('datetime__year', flat=True).distinct()
    
    # Get unique patients for filter (from details)
    patients = User.objects.filter(user_type='patient').order_by('first_name', 'last_name')
    
    # Get unique attendants for filter
    attendants = User.objects.filter(user_type='attendant').order_by('first_name', 'last_name')
    
    # Add pagination
    paginator = Paginator(history_logs, 20)  # 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'history_logs': page_obj,
        'page_obj': page_obj,
        'patient_filter': patient_filter,
        'treatment_filter': treatment_filter,
        'attendant_filter': attendant_filter,
        'year_filter': year_filter,
        'type_filter': type_filter,
        'years': years,
        'patients': patients,
        'attendants': attendants,
    }
    return render(request, 'appointments/admin_history_log.html', context)


@login_required
@user_passes_test(is_admin)
def admin_analytics(request):
    """Admin analytics dashboard - same as owner but for staff"""
    from analytics.services import AnalyticsService
    
    analytics_service = AnalyticsService()
    
    # Get comprehensive analytics data
    business_overview = analytics_service.get_business_overview()
    revenue_analytics = analytics_service.get_revenue_analytics()
    patient_analytics = analytics_service.get_patient_analytics()
    service_analytics = analytics_service.get_service_analytics()
    treatment_correlations = analytics_service.get_treatment_correlations()
    business_insights = analytics_service.get_business_insights()
    diagnostic_metrics = analytics_service.get_diagnostic_metrics()
    
    # Get filter parameters
    date_range = request.GET.get('date_range', '30')
    view_type = request.GET.get('view_type', 'overview')
    
    # Adjust date ranges based on filter
    if date_range == '7':
        days = 7
    elif date_range == '90':
        days = 90
    elif date_range == '365':
        days = 365
    else:
        days = 30
    
    context = {
        'business_overview': business_overview,
        'revenue_analytics': revenue_analytics,
        'patient_analytics': patient_analytics,
        'service_analytics': service_analytics,
        'treatment_correlations': treatment_correlations,
        'business_insights': business_insights,
        'diagnostic_metrics': diagnostic_metrics,
        'date_range': date_range,
        'view_type': view_type,
        'days': days,
    }
    
    return render(request, 'appointments/admin_analytics.html', context)

@login_required
@user_passes_test(is_admin)
def admin_update_stock(request, product_id):
    """Update product stock"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')  # 'add', 'minus', or 'set'
        quantity_raw = request.POST.get('quantity', '').strip()
        
        # Validate quantity input
        try:
            quantity = int(quantity_raw)
        except (TypeError, ValueError):
            messages.error(request, 'Please enter a valid whole number for the quantity.')
            return redirect('appointments:admin_inventory')
        
        if quantity < 0:
            messages.error(request, 'Quantity cannot be negative.')
            return redirect('appointments:admin_inventory')
        
        old_stock = product.stock  # Store old stock before changes
        
        if action == 'add':
            product.stock += quantity
            product.save()  # Save immediately after updating stock
            
            messages.success(request, f'Added {quantity} unit{"s" if quantity != 1 else ""} to {product.product_name}. New stock: {product.stock}')
            
            # Log the stock addition
            log_stock_change(
                product=product,
                action='add',
                quantity_change=quantity,
                previous_stock=old_stock,
                new_stock=product.stock,
                staff=request.user,
                reason=f"Stock manually added via inventory: {old_stock} → {product.stock}"
            )
            
        elif action == 'minus':
            if quantity > product.stock:
                messages.error(request, f'Cannot reduce by {quantity} units. Current stock is only {product.stock} units.')
                return redirect('appointments:admin_inventory')
            
            product.stock -= quantity
            product.save()  # Save immediately after updating stock
            
            messages.success(request, f'Reduced {quantity} unit{"s" if quantity != 1 else ""} from {product.product_name}. New stock: {product.stock}')
            
            # Log the stock reduction
            log_stock_change(
                product=product,
                action='minus',
                quantity_change=-quantity,
                previous_stock=old_stock,
                new_stock=product.stock,
                staff=request.user,
                reason=f"Stock manually reduced via inventory: {old_stock} → {product.stock}"
            )
            
        elif action == 'set':
            product.stock = quantity
            product.save()  # Save immediately after updating stock
            
            messages.success(request, f'Stock for {product.product_name} set to {quantity}')
            
            # Determine if it's an increase or decrease
            if quantity > old_stock:
                action_type = 'add'
                qty_change = quantity - old_stock
                reason = f"Stock manually set via inventory: {old_stock} → {quantity}"
            elif quantity < old_stock:
                action_type = 'minus'
                qty_change = old_stock - quantity
                reason = f"Stock manually reduced via inventory: {old_stock} → {quantity}"
            else:
                # No change
                action_type = None
            
            # Log only if there was a change
            if action_type:
                log_stock_change(
                    product=product,
                    action=action_type,
                    quantity_change=qty_change if action_type == 'add' else -qty_change,
                    previous_stock=old_stock,
                    new_stock=quantity,
                    staff=request.user,
                    reason=reason
                )
        else:
            messages.error(request, 'Unknown stock action. Please try again.')
            return redirect('appointments:admin_inventory')
        
        # Check if product is now available for ordering
        if product.stock > 0 and product.stock < 10:
            messages.warning(request, f'{product.product_name} is running low on stock ({product.stock} units remaining).')
        elif product.stock == 0:
            messages.info(request, f'{product.product_name} is now out of stock. Patients will be unable to order until replenished.')
        
        return redirect('appointments:admin_inventory')
    
    return redirect('appointments:admin_inventory')


def log_admin_history(item_type, item_name, action, performed_by, details='', related_id=None):
    """Helper function to log history"""
    from services.models import HistoryLog
    
    HistoryLog.objects.create(
        type=item_type,
        name=item_name,
        action=action,
        performed_by=performed_by,
        details=details,
        related_id=related_id
    )


@login_required
@user_passes_test(is_admin)
def admin_manage_services(request):
    """Staff manage services - same interface as owner"""
    from services.models import Service, ServiceCategory
    from django.core.paginator import Paginator
    
    services = Service.objects.filter(archived=False).order_by('service_name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            service_name = request.POST.get('service_name')
            description = request.POST.get('description')
            price = request.POST.get('price')
            duration = request.POST.get('duration')
            category_id = request.POST.get('category')
            
            if service_name and price and duration:
                try:
                    service = Service.objects.create(
                        service_name=service_name,
                        description=description,
                        price=price,
                        duration=duration,
                        category_id=category_id
                    )
                    log_admin_history('Service', service_name, 'Added', request.user.get_full_name() or request.user.username, 
                               f'Price: {price}, Duration: {duration}', service.id)
                    messages.success(request, 'Service added successfully!')
                except Exception as e:
                    messages.error(request, f'Error adding service: {str(e)}')
            else:
                messages.error(request, 'Please fill in all required fields.')
        
        elif action == 'edit':
            service_id = request.POST.get('service_id')
            service = get_object_or_404(Service, id=service_id)
            old_name = service.service_name
            service.service_name = request.POST.get('service_name', service.service_name)
            service.description = request.POST.get('description', service.description)
            price = request.POST.get('price')
            if price:
                service.price = price
            duration = request.POST.get('duration')
            if duration:
                service.duration = duration
            category_id = request.POST.get('category')
            if category_id:
                service.category_id = category_id
            service.save()
            log_admin_history('Service', service.service_name, 'Edited', request.user.get_full_name() or request.user.username,
                       f'Updated: {old_name} -> {service.service_name}', service.id)
            messages.success(request, 'Service updated successfully!')
        
        elif action == 'delete' or action == 'archive':
            service_id = request.POST.get('service_id')
            service = get_object_or_404(Service, id=service_id)
            service_name = service.service_name
            service.archived = True
            service.save()
            log_admin_history('Service', service_name, 'Deleted', request.user.get_full_name() or request.user.username,
                       f'Service archived', service.id)
            messages.success(request, 'Service archived successfully!')
        
        return redirect('appointments:admin_manage_services')
    
    # Add pagination
    paginator = Paginator(services, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = ServiceCategory.objects.all()
    context = {
        'services': page_obj,
        'page_obj': page_obj,
        'categories': categories,
    }
    return render(request, 'appointments/admin_manage_services.html', context)


@login_required
@user_passes_test(is_admin)
def admin_manage_packages(request):
    """Staff manage packages - same interface as owner with services"""
    from packages.models import Package, PackageService
    from services.models import Service
    from django.core.paginator import Paginator
    
    packages = Package.objects.filter(archived=False).order_by('package_name')
    all_services = Service.objects.filter(archived=False).order_by('service_name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            package_name = request.POST.get('package_name')
            description = request.POST.get('description')
            price = request.POST.get('price')
            sessions = request.POST.get('sessions')
            duration_days = request.POST.get('duration_days')
            grace_period_days = request.POST.get('grace_period_days')
            service_ids = request.POST.getlist('service_ids')
            
            # Filter out empty service IDs and deduplicate preserving order
            service_ids = [sid for sid in service_ids if sid]
            service_ids = list(dict.fromkeys(service_ids))
            
            if package_name and price and sessions:
                try:
                    package = Package.objects.create(
                        package_name=package_name,
                        description=description,
                        price=price,
                        sessions=sessions,
                        duration_days=duration_days or 0,
                        grace_period_days=grace_period_days or 0
                    )
                    
                    # Add services to package
                    if service_ids:
                        services = Service.objects.filter(id__in=service_ids)
                        for idx, service in enumerate(services):
                            PackageService.objects.create(
                                package=package,
                                service=service
                            )
                    
                    log_admin_history('Package', package_name, 'Added', request.user.get_full_name() or request.user.username,
                               f'Price: {price}, Sessions: {sessions}, Services: {len(service_ids)}', package.id)
                    messages.success(request, 'Package added successfully!')
                except Exception as e:
                    messages.error(request, f'Error adding package: {str(e)}')
            else:
                messages.error(request, 'Please fill in all required fields.')
        
        elif action == 'edit':
            package_id = request.POST.get('package_id')
            package = get_object_or_404(Package, id=package_id)
            old_name = package.package_name
            package.package_name = request.POST.get('package_name', package.package_name)
            package.description = request.POST.get('description', package.description)
            price = request.POST.get('price')
            if price:
                package.price = price
            sessions = request.POST.get('sessions')
            if sessions:
                package.sessions = sessions
            duration_days = request.POST.get('duration_days')
            if duration_days:
                package.duration_days = duration_days
            grace_period_days = request.POST.get('grace_period_days')
            if grace_period_days:
                package.grace_period_days = grace_period_days
            package.save()
            
            # Update services
            service_ids = request.POST.getlist('service_ids')
            service_ids = [sid for sid in service_ids if sid]
            service_ids = list(dict.fromkeys(service_ids))
            
            # Remove old service relationships
            PackageService.objects.filter(package=package).delete()
            
            # Add new services
            if service_ids:
                services = Service.objects.filter(id__in=service_ids)
                for idx, service in enumerate(services):
                    PackageService.objects.create(
                        package=package,
                        service=service
                    )
            
            log_admin_history('Package', package.package_name, 'Edited', request.user.get_full_name() or request.user.username,
                       f'Updated: {old_name} -> {package.package_name}', package.id)
            messages.success(request, 'Package updated successfully!')
        
        elif action == 'delete' or action == 'archive':
            package_id = request.POST.get('package_id')
            package = get_object_or_404(Package, id=package_id)
            package_name = package.package_name
            package.archived = True
            package.save()
            log_admin_history('Package', package_name, 'Deleted', request.user.get_full_name() or request.user.username,
                       f'Package archived', package.id)
            messages.success(request, 'Package archived successfully!')
        
        return redirect('appointments:admin_manage_packages')
    
    # Add pagination
    paginator = Paginator(packages, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'packages': page_obj,
        'page_obj': page_obj,
        'all_services': all_services,
    }
    return render(request, 'appointments/admin_manage_packages.html', context)


@login_required
@user_passes_test(is_admin)
def admin_manage_products(request):
    """Staff manage products - same interface as owner"""
    from django.core.paginator import Paginator
    
    products = Product.objects.filter(archived=False).order_by('product_name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            product_name = request.POST.get('product_name')
            description = request.POST.get('description')
            price = request.POST.get('price')
            stock = request.POST.get('stock') or request.POST.get('stock_quantity')
            
            if product_name and price:
                try:
                    Product.objects.create(
                        product_name=product_name,
                        description=description,
                        price=price,
                        stock=stock or 0
                    )
                    log_admin_history('Product', product_name, 'Added', request.user.get_full_name() or request.user.username,
                               f'Price: {price}, Stock: {stock or 0}', None)
                    messages.success(request, 'Product added successfully!')
                except Exception as e:
                    messages.error(request, f'Error adding product: {str(e)}')
            else:
                messages.error(request, 'Please fill in all required fields.')
        
        elif action == 'edit':
            product_id = request.POST.get('product_id')
            product = get_object_or_404(Product, id=product_id)
            old_name = product.product_name
            old_stock = product.stock  # Store old stock before changes
            
            product.product_name = request.POST.get('product_name', product.product_name)
            product.description = request.POST.get('description', product.description)
            price = request.POST.get('price')
            if price:
                product.price = price
            
            stock = request.POST.get('stock') or request.POST.get('stock_quantity')
            if stock is not None:
                new_stock = int(stock)
                if new_stock != old_stock:
                    # Determine action type
                    if new_stock > old_stock:
                        action_type = 'add'
                        quantity_change = new_stock - old_stock
                        reason = f"Stock added by staff: {old_stock} → {new_stock}"
                    else:
                        action_type = 'minus'
                        quantity_change = old_stock - new_stock
                        reason = f"Stock reduced by staff: {old_stock} → {new_stock}"
                    
                    # Log the stock change
                    log_stock_change(
                        product=product,
                        action=action_type,
                        quantity_change=quantity_change if action_type == 'add' else -quantity_change,
                        previous_stock=old_stock,
                        new_stock=new_stock,
                        staff=request.user,
                        reason=reason
                    )
                
                product.stock = new_stock
            
            product.save()
            log_admin_history('Product', product.product_name, 'Edited', request.user.get_full_name() or request.user.username,
                       f'Updated: {old_name} -> {product.product_name}', product.id)
            messages.success(request, 'Product updated successfully!')
        
        elif action == 'delete' or action == 'archive':
            product_id = request.POST.get('product_id')
            product = get_object_or_404(Product, id=product_id)
            product_name = product.product_name
            product.archived = True
            product.save()
            log_admin_history('Product', product_name, 'Deleted', request.user.get_full_name() or request.user.username,
                       f'Product archived', product.id)
            messages.success(request, 'Product archived successfully!')
        
        return redirect('appointments:admin_manage_products')
    
    # Add pagination
    paginator = Paginator(products, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'page_obj': page_obj,
    }
    return render(request, 'appointments/admin_manage_products.html', context)


@login_required
@user_passes_test(is_admin)
def admin_add_timeslot(request):
    """Add new time slot"""
    from .models import TimeSlot
    from datetime import datetime
    
    if request.method == 'POST':
        time_str = request.POST.get('time')
        is_active = request.POST.get('is_active') == '1'
        
        if time_str:
            try:
                # Parse the time string
                time_obj = datetime.strptime(time_str, '%H:%M').time()
                
                # Validate time is between 10:00 AM and 5:00 PM
                if time_obj.hour < 10 or time_obj.hour > 17:
                    messages.error(request, 'Time slot must be between 10:00 AM and 5:00 PM')
                    return redirect('appointments:admin_settings')
                
                # Check if time slot already exists
                if TimeSlot.objects.filter(time=time_obj).exists():
                    messages.error(request, f'Time slot {time_obj.strftime("%I:%M %p")} already exists')
                    return redirect('appointments:admin_settings')
                
                # Create time slot
                TimeSlot.objects.create(
                    time=time_obj,
                    is_active=is_active
                )
                
                log_admin_history(
                    'Time Slot',
                    time_obj.strftime('%I:%M %p'),
                    'Created',
                    request.user.get_full_name() or request.user.username,
                    f'Added time slot: {time_obj.strftime("%I:%M %p")} - {"Active" if is_active else "Inactive"}'
                )
                
                messages.success(request, f'Time slot {time_obj.strftime("%I:%M %p")} added successfully!')
            except ValueError:
                messages.error(request, 'Invalid time format')
        else:
            messages.error(request, 'Time is required')
    
    return redirect('appointments:admin_settings')


@login_required
@user_passes_test(is_admin)
def admin_toggle_timeslot(request, timeslot_id):
    """Toggle time slot active status"""
    from .models import TimeSlot
    
    timeslot = get_object_or_404(TimeSlot, id=timeslot_id)
    old_status = 'Active' if timeslot.is_active else 'Inactive'
    timeslot.is_active = not timeslot.is_active
    timeslot.save()
    
    new_status = 'Active' if timeslot.is_active else 'Inactive'
    
    log_admin_history(
        'Time Slot',
        timeslot.time.strftime('%I:%M %p'),
        'Edited',
        request.user.get_full_name() or request.user.username,
        f'Status changed: {old_status} → {new_status}'
    )
    
    messages.success(request, f'Time slot {timeslot.time.strftime("%I:%M %p")} is now {new_status.lower()}')
    return redirect('appointments:admin_settings')


@login_required
@user_passes_test(is_admin)
def admin_delete_timeslot(request, timeslot_id):
    """Delete time slot"""
    from .models import TimeSlot
    
    timeslot = get_object_or_404(TimeSlot, id=timeslot_id)
    time_display = timeslot.time.strftime('%I:%M %p')
    
    log_admin_history(
        'Time Slot',
        time_display,
        'Deleted',
        request.user.get_full_name() or request.user.username,
        f'Deleted time slot: {time_display}'
    )
    
    timeslot.delete()
    messages.success(request, f'Time slot {time_display} deleted successfully!')
    return redirect('appointments:admin_settings')


@login_required
@user_passes_test(is_admin)
def admin_edit_package_config(request, package_id):
    """Edit package configuration (sessions, duration, grace period)"""
    from packages.models import Package
    
    package = get_object_or_404(Package, id=package_id)
    
    if request.method == 'POST':
        sessions = request.POST.get('sessions')
        duration_days = request.POST.get('duration_days')
        grace_period_days = request.POST.get('grace_period_days')
        
        old_config = f'Sessions: {package.sessions}, Duration: {package.duration_days} days, Grace: {package.grace_period_days} days'
        
        if sessions and duration_days and grace_period_days:
            try:
                package.sessions = int(sessions)
                package.duration_days = int(duration_days)
                package.grace_period_days = int(grace_period_days)
                package.save()
                
                new_config = f'Sessions: {package.sessions}, Duration: {package.duration_days} days, Grace: {package.grace_period_days} days'
                
                log_admin_history(
                    'Package',
                    package.package_name,
                    'Edited',
                    request.user.get_full_name() or request.user.username,
                    f'Configuration updated: {old_config} → {new_config}',
                    package.id
                )
                
                messages.success(request, f'Package "{package.package_name}" configuration updated successfully!')
            except ValueError:
                messages.error(request, 'Invalid values provided. Please enter valid numbers.')
        else:
            messages.error(request, 'All fields are required')
    
    return redirect('appointments:admin_settings')

# Room Management Views
@login_required(login_url='/accounts/login/')
@user_passes_test(is_admin)
def admin_rooms(request):
    """View and manage all rooms"""
    from .models import Room
    
    rooms = Room.objects.all().order_by('name')
    
    context = {
        'rooms': rooms,
    }
    
    return render(request, 'appointments/admin_rooms.html', context)


@login_required(login_url='/accounts/login/')
@user_passes_test(is_admin)
def admin_add_room(request):
    """Add a new room"""
    from .models import Room
    
    if request.method == 'POST':
        room_name = request.POST.get('room_name', '').strip()
        is_available = request.POST.get('is_available') == 'on'
        
        if room_name:
            room, created = Room.objects.get_or_create(
                name=room_name,
                defaults={'is_available': is_available}
            )
            
            if created:
                messages.success(request, f'Room "{room_name}" added successfully!')
            else:
                messages.warning(request, f'Room "{room_name}" already exists!')
        else:
            messages.error(request, 'Room name is required.')
    
    return redirect('appointments:admin_rooms')


@login_required(login_url='/accounts/login/')
@user_passes_test(is_admin)
def admin_edit_room(request, room_id):
    """Edit room details"""
    from .models import Room
    
    room = get_object_or_404(Room, id=room_id)
    
    if request.method == 'POST':
        room_name = request.POST.get('room_name', '').strip()
        is_available = request.POST.get('is_available') == 'on'
        
        if room_name:
            old_name = room.name
            room.name = room_name
            room.is_available = is_available
            room.save()
            
            messages.success(request, f'Room updated successfully!')
        else:
            messages.error(request, 'Room name is required.')
    
    return redirect('appointments:admin_rooms')


@login_required(login_url='/accounts/login/')
@user_passes_test(is_admin)
def admin_toggle_room(request, room_id):
    """Toggle room availability"""
    from .models import Room
    
    room = get_object_or_404(Room, id=room_id)
    old_status = room.is_available
    room.is_available = not room.is_available
    room.save()
    
    status_text = 'enabled' if room.is_available else 'disabled'
    messages.success(request, f'Room "{room.name}" has been {status_text}.')
    
    return redirect('appointments:admin_rooms')


@login_required(login_url='/accounts/login/')
@user_passes_test(is_admin)
def admin_delete_room(request, room_id):
    """Delete a room"""
    from .models import Room
    
    room = get_object_or_404(Room, id=room_id)
    room_name = room.name
    room.delete()
    
    messages.success(request, f'Room "{room_name}" has been deleted.')
    
    return redirect('appointments:admin_rooms')