from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from accounts.models import User
from appointments.models import Appointment, Notification
import json
from django.conf import settings
from datetime import datetime, timedelta
from django.db import transaction
from appointments.models import Diagnosis
from .forms import DiagnosisForm


def is_attendant(user):
    """Check if user is attendant"""
    return user.is_authenticated and user.user_type == 'attendant'


@login_required(login_url='/accounts/login/attendant/')
@user_passes_test(is_attendant, login_url='/accounts/login/attendant/')
def attendant_dashboard(request):
    """Attendant dashboard - View appointments they are in charge of"""
    today = timezone.now().date()
    
    # Get today's appointments - show all appointments for today that have this attendant assigned
    today_appointments = (
        Appointment.objects.filter(
            appointment_date=today,
            attendant=request.user
        )
        .select_related('patient', 'service', 'product', 'package', 'room')
        .order_by('appointment_time')
    )
    
    # Get upcoming appointments (next 7 days) - show all with this attendant assigned
    upcoming_appointments = (
        Appointment.objects.filter(
            appointment_date__gte=today,
            appointment_date__lte=today + timezone.timedelta(days=7),
            status__in=['scheduled', 'confirmed', 'pending', 'approved'],
            attendant=request.user
        )
        .select_related('patient', 'service', 'product', 'package', 'room')
        .order_by('appointment_date', 'appointment_time')
    )
    
    # Get notifications regarding appointments this attendant is in charge of
    notifications = Notification.objects.filter(
        type__in=['appointment', 'confirmation', 'cancellation']
    ).order_by('-created_at')[:3]
    
    # Statistics for this attendant
    total_appointments = Appointment.objects.filter(attendant=request.user).count()
    today_count = today_appointments.count()
    upcoming_count = upcoming_appointments.count()
    
    # Get notification count
    notification_count = Notification.objects.filter(
        patient=request.user,
        is_read=False
    ).count()
    
    # Get recent patient feedback for appointments assigned to this attendant ONLY
    from appointments.models import Feedback
    recent_feedbacks = []
    feedback_count = 0
    
    if request.user.user_type == 'attendant':
        # Only show feedback for appointments assigned to this specific attendant
        recent_feedbacks = Feedback.objects.filter(
            appointment__attendant=request.user,
            attendant_rating__isnull=False
        ).select_related('patient', 'appointment').order_by('-created_at')[:5]
        
        feedback_count = Feedback.objects.filter(
            appointment__attendant=request.user,
            attendant_rating__isnull=False
        ).count()
    else:
        # If no attendant object found, don't show any feedback
        # This ensures privacy - only show feedback when we can verify the attendant
        recent_feedbacks = []
        feedback_count = 0
    
    context = {
        'today_appointments': today_appointments,
        'upcoming_appointments': upcoming_appointments,
        'notifications': notifications,
        'total_appointments': total_appointments,
        'today_count': today_count,
        'upcoming_count': upcoming_count,
        'today': today,
        'notification_count': notification_count,
        'recent_feedbacks': recent_feedbacks,
        'feedback_count': feedback_count,
    }
    
    return render(request, 'attendant/dashboard.html', context)


@login_required(login_url='/accounts/login/attendant/')
@user_passes_test(is_attendant, login_url='/accounts/login/attendant/')
def attendant_appointments(request):
    """Attendant appointments management - Only shows appointments assigned to this attendant"""
    from django.core.paginator import Paginator
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    search_query = request.GET.get('search', '')
    
    # Start with appointments assigned to this attendant - use select_related to avoid N+1 queries
    appointments = (
        Appointment.objects
        .filter(attendant=request.user)
        .select_related('patient', 'service', 'product', 'package', 'room')
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
    
    # Add pagination to limit query size
    paginator = Paginator(appointments, 25)  # 25 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # compute diagnose window flags for appointments in the current page for UX
    now = timezone.now()
    PRE = getattr(settings, 'APPOINTMENT_DIAGNOSE_PRE_WINDOW_MINUTES', 0)
    POST = getattr(settings, 'APPOINTMENT_DIAGNOSE_POST_WINDOW_MINUTES', 30)
    for appt in page_obj.object_list:
        try:
            appt_dt = datetime.combine(appt.appointment_date, appt.appointment_time)
            appt_dt = timezone.make_aware(appt_dt, timezone.get_current_timezone())
        except Exception:
            appt_dt = None

        if appt_dt:
            start = appt_dt - timedelta(minutes=PRE)
            end = appt_dt + timedelta(minutes=POST)
            # Only allow diagnose if within window, owned by user, status is scheduled/confirmed,
            # and no diagnosis already exists for this appointment (separate from timer logic).
            try:
                _ = appt.diagnosis
                has_diag = True
            except Diagnosis.DoesNotExist:
                has_diag = False

            appt.can_diagnose = (start <= now <= end) and (appt.attendant == request.user) and (appt.status in ['scheduled', 'confirmed']) and (not has_diag)
        else:
            appt.can_diagnose = False

    context = {
        'appointments': page_obj,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'search_query': search_query,
    }
    
    return render(request, 'attendant/appointments.html', context)


@login_required(login_url='/accounts/login/attendant/')
@user_passes_test(is_attendant, login_url='/accounts/login/attendant/')
def attendant_appointment_detail(request, appointment_id):
    """Attendant view appointment details - Only for assigned appointments"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Verify user is an attendant
    if request.user.user_type != 'attendant':
        messages.error(request, 'No attendant profile found. Please contact staff.')
        return redirect('attendant:dashboard')
    
    # Verify appointment is assigned to this attendant
    if appointment.attendant != request.user:
        messages.error(request, 'You can only view appointments assigned to you.')
        return redirect('attendant:appointments')
    
    # Get feedback for this appointment
    from appointments.models import Feedback
    feedback = None
    attendant_feedback = None
    try:
        feedback = Feedback.objects.get(appointment=appointment)
        # Separate service/package/product feedback from attendant feedback
        attendant_feedback = {
            'rating': feedback.attendant_rating,
            'comment': feedback.comment if feedback.attendant_rating else None
        }
    except Feedback.DoesNotExist:
        pass
    
    context = {
        'appointment': appointment,
        'feedback': feedback,
        'attendant_feedback': attendant_feedback,
    }
    # compute whether Diagnose action should be available for this appointment
    try:
        appt_dt = datetime.combine(appointment.appointment_date, appointment.appointment_time)
        appt_dt = timezone.make_aware(appt_dt, timezone.get_current_timezone())
    except Exception:
        appt_dt = None

    PRE = getattr(settings, 'APPOINTMENT_DIAGNOSE_PRE_WINDOW_MINUTES', 0)
    POST = getattr(settings, 'APPOINTMENT_DIAGNOSE_POST_WINDOW_MINUTES', 30)
    now = timezone.now()
    if appt_dt:
        start = appt_dt - timedelta(minutes=PRE)
        end = appt_dt + timedelta(minutes=POST)
        context['can_diagnose'] = (start <= now <= end) and (appointment.attendant == request.user) and (appointment.status in ['scheduled', 'confirmed'])
    else:
        context['can_diagnose'] = False
    
    return render(request, 'attendant/appointment_detail.html', context)


@login_required(login_url='/accounts/login/attendant/')
@user_passes_test(is_attendant, login_url='/accounts/login/attendant/')
def attendant_diagnose_appointment(request, appointment_id):
    """Render and handle diagnosis form for an appointment."""
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Verify attendant ownership
    if appointment.attendant != request.user:
        messages.error(request, 'You can only diagnose appointments assigned to you.')
        return redirect('attendant:appointments')

    # Time window enforcement (only on GET). Allow POST to proceed to avoid tiny timing drift blocking submission.
    try:
        appt_dt = datetime.combine(appointment.appointment_date, appointment.appointment_time)
        appt_dt = timezone.make_aware(appt_dt, timezone.get_current_timezone())
    except Exception:
        appt_dt = None

    PRE = getattr(settings, 'APPOINTMENT_DIAGNOSE_PRE_WINDOW_MINUTES', 0)
    POST = getattr(settings, 'APPOINTMENT_DIAGNOSE_POST_WINDOW_MINUTES', 30)
    now = timezone.now()
    if request.method != 'POST':
        if not appt_dt or not (appt_dt - timedelta(minutes=PRE) <= now <= appt_dt + timedelta(minutes=POST)):
            messages.error(request, 'Diagnosis can only be started at the appointment time.')
            return redirect('attendant:appointment_detail', appointment_id=appointment_id)

    # Prevent multiple diagnoses race
    if request.method == 'POST':
        form = DiagnosisForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Persist all submitted fields so diagnosis details are saved correctly
                defaults = {
                    'diagnosed_by': request.user,
                    'diagnosis_date': appointment.appointment_date,
                    'diagnosis_time': appointment.appointment_time,
                    'blood_pressure': form.cleaned_data.get('blood_pressure'),
                    'skin_type': form.cleaned_data.get('skin_type'),
                    'lesion_type': form.cleaned_data.get('lesion_type'),
                    'target_area': form.cleaned_data.get('target_area'),
                    'keloid_risk': form.cleaned_data.get('keloid_risk'),
                    'accutane_history': form.cleaned_data.get('accutane_history'),
                    'notes': form.cleaned_data.get('notes'),
                    'prescription': form.cleaned_data.get('prescription'),
                    'follow_up_recommended': form.cleaned_data.get('follow_up_recommended')
                }

                diagnosis, created = Diagnosis.objects.get_or_create(
                    appointment=appointment,
                    defaults=defaults
                )

                if not created:
                    # Update existing diagnosis with all fields from the form
                    diagnosis.diagnosed_by = request.user
                    diagnosis.blood_pressure = form.cleaned_data.get('blood_pressure')
                    diagnosis.skin_type = form.cleaned_data.get('skin_type')
                    diagnosis.lesion_type = form.cleaned_data.get('lesion_type')
                    diagnosis.target_area = form.cleaned_data.get('target_area')
                    diagnosis.keloid_risk = form.cleaned_data.get('keloid_risk')
                    diagnosis.accutane_history = form.cleaned_data.get('accutane_history')
                    diagnosis.notes = form.cleaned_data.get('notes')
                    diagnosis.prescription = form.cleaned_data.get('prescription')
                    diagnosis.follow_up_recommended = form.cleaned_data.get('follow_up_recommended')
                    if not diagnosis.diagnosis_date:
                        diagnosis.diagnosis_date = appointment.appointment_date
                    if not diagnosis.diagnosis_time:
                        diagnosis.diagnosis_time = appointment.appointment_time
                    diagnosis.save()

            messages.success(request, 'Diagnosis saved. Proceed to perform service.')
            return redirect('attendant:perform_service', appointment_id=appointment.id)
    else:
        # Prepopulate form if diagnosis exists
        try:
            existing = appointment.diagnosis
            form = DiagnosisForm(instance=existing)
        except Diagnosis.DoesNotExist:
            form = DiagnosisForm()

    context = {
        'appointment': appointment,
        'form': form,
    }
    return render(request, 'attendant/diagnose_form.html', context)


@login_required(login_url='/accounts/login/attendant/')
@user_passes_test(is_attendant, login_url='/accounts/login/attendant/')
def attendant_perform_service(request, appointment_id):
    """Waiting/perform service page. 'Done' button finalizes the appointment."""
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Verify attendant
    if appointment.attendant != request.user:
        messages.error(request, 'You can only perform services for appointments assigned to you.')
        return redirect('attendant:appointments')

    if request.method == 'POST':
        # Finalize: mark appointment completed and redirect
        appointment.status = 'completed'
        appointment.save()
        messages.success(request, 'Service marked as done.')
        return redirect('attendant:appointment_detail', appointment_id=appointment_id)

    context = {
        'appointment': appointment,
    }
    return render(request, 'attendant/perform_service.html', context)


@login_required(login_url='/accounts/login/attendant/')
@user_passes_test(is_attendant, login_url='/accounts/login/attendant/')
def attendant_confirm_appointment(request, appointment_id):
    """Attendant confirm an appointment - Only for assigned appointments"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Verify user is an attendant
    if request.user.user_type != 'attendant':
        messages.error(request, 'No attendant profile found. Please contact staff.')
        return redirect('attendant:dashboard')
    
    # Verify appointment is assigned to this attendant
    if appointment.attendant != request.user:
        messages.error(request, 'You can only confirm appointments assigned to you.')
        return redirect('attendant:appointments')
    
    if appointment.status == 'scheduled':
        appointment.status = 'confirmed'
        appointment.save()
        
        # If this is a product order, deduct stock
        if appointment.product:
            product = appointment.product
            if product.stock > 0:
                product.stock -= 1
                product.save()
        
        # Get attendant name for notification
        attendant_name = f"{appointment.attendant.first_name} {appointment.attendant.last_name}"
        
        # Create notification for patient
        Notification.objects.create(
            type='confirmation',
            appointment_id=appointment.id,
            title='Appointment Confirmed',
            message=f'Your appointment for {appointment.get_service_name()} on {appointment.appointment_date} at {appointment.appointment_time} has been confirmed by your attendant {attendant_name}.',
            patient=appointment.patient
        )
        
        messages.success(request, f'Appointment for {appointment.patient.full_name} has been confirmed.')
    else:
        messages.error(request, 'Only scheduled appointments can be confirmed.')
    
    return redirect('attendant:appointment_detail', appointment_id=appointment_id)


@login_required(login_url='/accounts/login/attendant/')
@user_passes_test(is_attendant, login_url='/accounts/login/attendant/')
def attendant_complete_appointment(request, appointment_id):
    """Attendant mark appointment as completed and save treatment details - Only for assigned appointments"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Verify user is an attendant
    if request.user.user_type != 'attendant':
        messages.error(request, 'No attendant profile found. Please contact staff.')
        return redirect('attendant:dashboard')
    
    # Verify appointment is assigned to this attendant
    if appointment.attendant != request.user:
        messages.error(request, 'You can only complete appointments assigned to you.')
        return redirect('attendant:appointments')
    
    # Verify that the current date matches the appointment date
    today = timezone.now().date()
    if appointment.appointment_date != today:
        messages.error(request, f'Appointment can only be marked on the appointment date ({appointment.appointment_date}). Today is {today}.')
        return redirect('attendant:appointment_detail', appointment_id=appointment_id)
    
    if request.method == 'POST':
        action = request.POST.get('action', 'mark_completed')
        
        if action == 'mark_completed':
            # First step: Mark appointment as completed
            if appointment.status in ['scheduled', 'confirmed']:
                appointment.status = 'completed'
                appointment.save()
                messages.success(request, 'Appointment marked as completed! You can now fill in treatment details.')
            else:
                messages.error(request, 'This appointment has already been completed.')
                
        elif action == 'treatment_done':
            # Second step: Save treatment details and notify patient
            if appointment.status == 'completed':
                from appointments.models import Treatment
                
                # Get treatment details from form (if modal was used)
                treatment_notes = request.POST.get('treatment_notes', '').strip()
                products_used = request.POST.get('products_used', '').strip()
                duration_minutes = request.POST.get('duration_minutes', '').strip()
                next_appointment_recommended = request.POST.get('next_appointment_recommended', '').strip()
            
            treatment, created = Treatment.objects.get_or_create(
                appointment=appointment,
                defaults={
                    'treatment_date': appointment.appointment_date,
                    'treatment_time': appointment.appointment_time,
                    'notes': treatment_notes if treatment_notes else None,
                    'products_used': products_used if products_used else None,
                    'duration_minutes': int(duration_minutes) if duration_minutes and duration_minutes.isdigit() else None,
                    'next_appointment_recommended': next_appointment_recommended if next_appointment_recommended else None,
                }
            )
            
            # Update if treatment already exists
            if not created:
                if treatment_notes:
                    treatment.notes = treatment_notes
                if products_used:
                    treatment.products_used = products_used
                if duration_minutes and duration_minutes.isdigit():
                    treatment.duration_minutes = int(duration_minutes)
                if next_appointment_recommended:
                    treatment.next_appointment_recommended = next_appointment_recommended
                treatment.save()
                
                # Create notification for patient prompting them to rate/leave feedback
                Notification.objects.create(
                    type='appointment',
                    appointment_id=appointment.id,
                    title='Treatment Completed - Please Rate Your Experience',
                    message=f'Your treatment for {appointment.get_service_name()} on {appointment.appointment_date} has been completed. Please rate your experience and leave feedback to help us improve our services!',
                    patient=appointment.patient
                )
                
                messages.success(request, f'Treatment completed for {appointment.patient.full_name}. Patient has been notified to rate their experience.')
            else:
                messages.error(request, 'Appointment must be marked as completed first.')
    else:
        messages.error(request, 'Invalid request method.')
    
    return redirect('attendant:appointment_detail', appointment_id=appointment_id)


@login_required(login_url='/accounts/login/attendant/')
@user_passes_test(is_attendant, login_url='/accounts/login/attendant/')
def attendant_patient_profile(request, patient_id):
    """Attendant view patient profile - Only for patients with assigned appointments"""
    patient = get_object_or_404(User, id=patient_id, user_type='patient')
    
    # Verify user is an attendant
    if request.user.user_type != 'attendant':
        messages.error(request, 'No attendant profile found. Please contact staff.')
        return redirect('attendant:dashboard')
    
    # Verify patient has assigned appointment with this attendant (Data Privacy compliance)
    if not Appointment.objects.filter(patient=patient, attendant=request.user).exists():
        messages.error(request, 'You can only view patient profiles for appointments assigned to you.')
        return redirect('attendant:dashboard')
    
    # Get patient's appointments assigned to this attendant only
    appointments = Appointment.objects.filter(
        patient=patient,
        attendant=request.user
    ).order_by('-appointment_date')
    
    # Get patient's packages (if any)
    packages = []  # Simplified for now
    
    context = {
        'patient': patient,
        'appointments': appointments,
        'packages': packages,
    }
    
    return render(request, 'attendant/patient_profile.html', context)


@login_required(login_url='/accounts/login/attendant/')
@user_passes_test(is_attendant, login_url='/accounts/login/attendant/')
def attendant_history(request):
    """Attendant view own history of completed appointments only"""
    # Verify user is an attendant
    if request.user.user_type != 'attendant':
        messages.error(request, 'No attendant profile found. Please contact staff.')
        return redirect('attendant:dashboard')
    
    # Get only completed appointments assigned to this attendant
    completed_appointments = Appointment.objects.filter(
        attendant=request.user,
        status='completed'
    ).order_by('-appointment_date', '-appointment_time')
    
    context = {
        'completed_appointments': completed_appointments,
    }
    
    return render(request, 'attendant/history.html', context)


@login_required(login_url='/accounts/login/attendant/')
@user_passes_test(is_attendant, login_url='/accounts/login/attendant/')
def attendant_feedback(request):
    """Attendant view own feedback from patients - ONLY shows feedback for their own appointments"""
    # Verify user is an attendant
    if request.user.user_type != 'attendant':
        messages.error(request, 'No attendant profile found. Please contact staff to set up your attendant profile.')
        return redirect('attendant:dashboard')
    
    # Get feedback ONLY for appointments assigned to THIS specific attendant
    # This ensures each attendant only sees their own feedback
    from appointments.models import Feedback
    from django.db.models import Q
    
    # Get filter parameters
    rating_filter = request.GET.get('rating', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search_query = request.GET.get('search', '')
    
    feedbacks = Feedback.objects.filter(
        appointment__attendant=request.user,
        attendant_rating__isnull=False
    ).select_related('patient', 'appointment', 'appointment__attendant')
    
    # Apply filters
    if rating_filter:
        feedbacks = feedbacks.filter(attendant_rating=rating_filter)
    
    if date_from:
        feedbacks = feedbacks.filter(created_at__gte=date_from)
    
    if date_to:
        feedbacks = feedbacks.filter(created_at__lte=date_to)
    
    if search_query:
        feedbacks = feedbacks.filter(
            Q(patient__first_name__icontains=search_query) |
            Q(patient__last_name__icontains=search_query) |
            Q(comment__icontains=search_query) |
            Q(appointment__service__service_name__icontains=search_query) |
            Q(appointment__package__package_name__icontains=search_query)
        )
    
    feedbacks = feedbacks.order_by('-created_at')
    
    # Add pagination
    from django.core.paginator import Paginator
    paginator = Paginator(feedbacks, 20)  # 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'feedbacks': page_obj,
        'page_obj': page_obj,
        'attendant_obj': request.user,
        'rating_filter': rating_filter,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query,
    }
    
    return render(request, 'attendant/feedback.html', context)


@login_required(login_url='/accounts/login/attendant/')
@user_passes_test(is_attendant, login_url='/accounts/login/attendant/')
def attendant_schedule(request):
    """Attendant view and edit their availability schedule"""
    from accounts.models import AttendantProfile
    from datetime import datetime
    
    # Verify user is an attendant
    if request.user.user_type != 'attendant':
        messages.error(request, 'No attendant profile found. Please contact staff.')
        return redirect('attendant:dashboard')
    
    # Get or create attendant profile with work schedule
    try:
        profile = request.user.attendant_profile
    except AttendantProfile.DoesNotExist:
        profile = None
    
    if request.method == 'POST':
        work_days = request.POST.getlist('work_days')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        if not work_days:
            messages.error(request, 'Please select at least one work day.')
            context = {
                'attendant': request.user,
                'profile': profile,
            }
            return render(request, 'attendant/schedule.html', context)
        
        if not start_time or not end_time:
            messages.error(request, 'Please provide both start and end times.')
            context = {
                'attendant': request.user,
                'profile': profile,
            }
            return render(request, 'attendant/schedule.html', context)
        
        # Validate store hours restriction (10 AM - 6 PM)
        start_time_obj = datetime.strptime(start_time, '%H:%M').time()
        end_time_obj = datetime.strptime(end_time, '%H:%M').time()
        min_time = datetime.strptime('10:00', '%H:%M').time()
        max_time = datetime.strptime('18:00', '%H:%M').time()
        
        if start_time_obj < min_time or end_time_obj > max_time:
            messages.error(request, 'Shift hours must be between 10:00 AM and 6:00 PM.')
            context = {
                'attendant': request.user,
                'profile': profile,
            }
            return render(request, 'attendant/schedule.html', context)
        
        if start_time_obj >= end_time_obj:
            messages.error(request, 'Start time must be before end time.')
            context = {
                'attendant': request.user,
                'profile': profile,
            }
            return render(request, 'attendant/schedule.html', context)
        
        # Get or create profile
        profile, created = AttendantProfile.objects.get_or_create(user=request.user)
        profile.work_days = work_days
        profile.start_time = start_time
        profile.end_time = end_time
        profile.save()
        
        if created:
            messages.success(request, 'Your work schedule has been created successfully.')
        else:
            messages.success(request, 'Your work schedule has been updated successfully.')
        
        return redirect('attendant:schedule')
    
    context = {
        'attendant': request.user,
        'profile': profile,
    }
    
    return render(request, 'attendant/schedule.html', context)


@login_required(login_url='/accounts/login/attendant/')
@user_passes_test(is_attendant, login_url='/accounts/login/attendant/')
def attendant_manage_profile(request):
    """Attendant manage their own profile (edit name, email, phone, password, profile picture)"""
    import re
    from django.contrib.auth import update_session_auth_hash
    user = request.user
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        current_password = request.POST.get('current_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        profile_picture = request.FILES.get('profile_picture')
        
        # Validate required fields
        if not all([first_name, last_name, email]):
            messages.error(request, 'First name, last name, and email are required.')
            return redirect('attendant:manage_profile')
        
        # Validate email
        if not email or '@' not in email:
            messages.error(request, 'Please enter a valid email address.')
            return redirect('attendant:manage_profile')
        
        # Check if email is already taken by another user
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, 'This email is already in use by another account.')
            return redirect('attendant:manage_profile')
        
        # Validate that names contain only letters and spaces (no numbers, symbols, or hyphens)
        name_pattern = re.compile(r'^[A-Za-z\s]+$')
        
        if not name_pattern.match(first_name):
            messages.error(request, 'First name can only contain letters and spaces. No numbers, symbols, or hyphens allowed.')
            return redirect('attendant:manage_profile')
        
        if not name_pattern.match(last_name):
            messages.error(request, 'Last name can only contain letters and spaces. No numbers, symbols, or hyphens allowed.')
            return redirect('attendant:manage_profile')
        
        if middle_name and not name_pattern.match(middle_name):
            messages.error(request, 'Middle name can only contain letters and spaces. No numbers, symbols, or hyphens allowed.')
            return redirect('attendant:manage_profile')
        
        # Validate phone number (if provided)
        if phone:
            # Remove any non-digit characters
            phone_digits = re.sub(r'\D', '', phone)
            # Check if it's exactly 11 digits and starts with 09
            if len(phone_digits) != 11 or not phone_digits.startswith('09'):
                messages.error(request, 'Please enter a valid 11-digit Philippine phone number starting with 09 (e.g., 09123456789)')
                return redirect('attendant:manage_profile')
            phone = phone_digits
        
        # Handle password change if provided
        password_changed = False
        if new_password:
            if not current_password:
                messages.error(request, 'Please enter your current password to change it.')
                return redirect('attendant:manage_profile')
            
            # Verify current password
            if not user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
                return redirect('attendant:manage_profile')
            
            # Validate new password
            if len(new_password) < 8:
                messages.error(request, 'New password must be at least 8 characters long.')
                return redirect('attendant:manage_profile')
            
            if new_password != confirm_password:
                messages.error(request, 'New password and confirmation do not match.')
                return redirect('attendant:manage_profile')
            
            # Set new password
            user.set_password(new_password)
            password_changed = True
            messages.success(request, 'Password changed successfully.')
        
        # Update user fields
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.middle_name = middle_name if middle_name else ''
        user.phone = phone if phone else ''
        
        # Handle profile picture upload
        if profile_picture:
            # Validate file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if profile_picture.content_type not in allowed_types:
                messages.error(request, 'Invalid file type. Please upload a JPEG, PNG, GIF, or WebP image.')
                return redirect('attendant:manage_profile')
            
            # Validate file size (max 5MB)
            if profile_picture.size > 5 * 1024 * 1024:
                messages.error(request, 'Image file is too large. Maximum size is 5MB.')
                return redirect('attendant:manage_profile')
            
            user.profile_picture = profile_picture
            messages.success(request, 'Profile picture updated successfully.')
        
        user.save()
        
        # Update session if password was changed to prevent logout
        if password_changed:
            update_session_auth_hash(request, user)
        
        messages.success(request, 'Your profile has been updated successfully.')
        return redirect('attendant:manage_profile')
    
    context = {
        'user': user,
    }
    
    return render(request, 'attendant/manage_profile.html', context)


@login_required(login_url='/accounts/login/attendant/')
@user_passes_test(is_attendant, login_url='/accounts/login/attendant/')
def attendant_notifications(request):
    """Attendant notifications"""
    from django.db.models import Q
    
    # Show notifications assigned to this attendant or system notifications
    notifications = Notification.objects.filter(
        (Q(patient=request.user) | Q(patient__isnull=True)),
        type__in=['appointment', 'confirmation', 'cancellation', 'reschedule', 'system']
    ).order_by('-created_at')
    
    # Mark notifications as read
    unread_notifications = notifications.filter(is_read=False)
    for notification in unread_notifications:
        notification.is_read = True
        notification.save()
    
    context = {
        'notifications': notifications,
    }
    
    return render(request, 'attendant/notifications.html', context)


@login_required(login_url='/accounts/login/attendant/')
@user_passes_test(is_attendant, login_url='/accounts/login/attendant/')
def attendant_mark_notification_read(request, notification_id):
    """Mark notification as read"""
    notification = get_object_or_404(Notification, id=notification_id)
    notification.is_read = True
    notification.save()
    
    messages.success(request, 'Notification marked as read.')
    return redirect('attendant:notifications')
# Attendant leave request UI removed: use direct staff contact instead.


# API Endpoints for notifications
@csrf_exempt
@login_required(login_url='/accounts/login/attendant/')
@user_passes_test(is_attendant, login_url='/accounts/login/attendant/')
def get_notifications_api(request):
    """API endpoint to get notifications for attendant"""
    try:
        # Filter notifications for the current attendant user
        notifications = Notification.objects.filter(
            patient=request.user,
            type__in=['appointment', 'confirmation', 'cancellation']
        ).order_by('-created_at')[:20]
        
        unread_count = notifications.filter(is_read=False).count()
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'notification_id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'created_at_formatted': notification.created_at.strftime('%b %d, %Y %I:%M %p'),
                'is_read': notification.is_read,
                'type': notification.type
            })
        
        return JsonResponse({
            'success': True,
            'notifications': notifications_data,
            'unread_count': unread_count
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@login_required(login_url='/accounts/login/attendant/')
@user_passes_test(is_attendant, login_url='/accounts/login/attendant/')
def update_notifications_api(request):
    """API endpoint to update notifications"""
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'mark_read':
                notification_id = data.get('notification_id')
                if notification_id:
                    notification = get_object_or_404(Notification, id=notification_id)
                    notification.is_read = True
                    notification.save()
                    
            elif action == 'mark_all_read':
                Notification.objects.filter(
                    type__in=['appointment', 'confirmation', 'cancellation']
                ).update(is_read=True)
            
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid method'})
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
