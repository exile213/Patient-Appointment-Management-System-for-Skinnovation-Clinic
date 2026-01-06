from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import datetime, time as time_obj, date, time
from .models import Appointment, Notification, ClosedDay, CancellationRequest
from accounts.models import User, AttendantProfile
from services.models import Service
from products.models import Product
from packages.models import Package
from services.utils import send_appointment_sms, send_attendant_assignment_sms
import json
import logging

logger = logging.getLogger(__name__)


def get_available_attendants(selected_date=None, selected_time=None):
    """
    Get all available attendants (User objects with user_type='attendant').
    Only returns attendants whose User account is active.
    """
    # Get all active attendant users
    all_attendants = User.objects.filter(user_type='attendant', is_active=True).order_by('first_name', 'last_name')
    
    # If date and time are provided, filter by availability
    if selected_date and selected_time:
        try:
            appointment_datetime = datetime.strptime(f"{selected_date} {selected_time}", "%Y-%m-%d %H:%M")
            day_name = appointment_datetime.strftime('%A')
            appointment_time_obj = datetime.strptime(selected_time, "%H:%M").time()
            
            # Filter attendants by availability
            available_attendants = []
            for attendant_user in all_attendants:
                try:
                    profile = getattr(attendant_user, 'attendant_profile', None)
                    if profile:
                        # Only include if work_days is not empty and the selected day is in work_days
                        if profile.work_days and day_name in profile.work_days and profile.start_time <= appointment_time_obj < profile.end_time:
                            available_attendants.append(attendant_user)
                    # If no profile, exclude from available list (attendant must have profile with work days set)
                except Exception:
                    # If any error occurs, exclude this attendant
                    pass
            
            return User.objects.filter(id__in=[a.id for a in available_attendants]).order_by('first_name', 'last_name')
        except (ValueError, TypeError):
            # If date/time parsing fails, return only active attendants
            return all_attendants
    
    return all_attendants


@login_required
def my_appointments(request):
    """User's appointments"""
    appointments = Appointment.objects.filter(patient=request.user).order_by('-created_at', '-appointment_date', '-appointment_time')
    
    context = {
        'appointments': appointments,
    }
    
    return render(request, 'appointments/my_appointments.html', context)


@login_required
def patient_history(request):
    """Patient view own treatment and product purchase history"""
    # Only allow patients to access this
    if request.user.user_type != 'patient':
        messages.error(request, 'This page is only available for patients.')
        return redirect('home')
    
    # Get completed appointments (treatment history)
    completed_appointments = Appointment.objects.filter(
        patient=request.user,
        status='completed'
    ).order_by('-appointment_date', '-appointment_time')
    
    # Get product purchases (appointments with products)
    product_purchases = Appointment.objects.filter(
        patient=request.user,
        product__isnull=False
    ).order_by('-appointment_date', '-appointment_time')
    
    context = {
        'completed_appointments': completed_appointments,
        'product_purchases': product_purchases,
    }
    
    return render(request, 'appointments/patient_history.html', context)


@login_required
def book_service(request, service_id):
    """Book a service appointment"""
    service = get_object_or_404(Service, id=service_id)
    
    if request.method == 'POST':
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        attendant_id = request.POST.get('attendant', '')
        room_id = request.POST.get('room', '')
        
        if appointment_date and appointment_time:
            # Validate that date and time are not in the past
            from django.utils import timezone
            appointment_datetime_str = f"{appointment_date} {appointment_time}"
            try:
                appointment_datetime = datetime.strptime(appointment_datetime_str, "%Y-%m-%d %H:%M")
                appointment_datetime_aware = timezone.make_aware(appointment_datetime)
                
                if appointment_datetime_aware <= timezone.now():
                    messages.error(request, 'Cannot book appointments in the past. Time has already passed. Please select a future date and time.')
                    context = {
                        'service': service,
                        'attendants': get_available_attendants(),
                    }
                    return render(request, 'appointments/book_service.html', context)
            except ValueError:
                messages.error(request, 'Invalid date or time format.')
                context = {
                    'service': service,
                    'attendants': get_available_attendants(),
                }
                return render(request, 'appointments/book_service.html', context)
            
            # Check if the selected date is a closed clinic day
            appointment_date_obj = datetime.strptime(appointment_date, "%Y-%m-%d").date()
            if ClosedDay.objects.filter(date=appointment_date_obj).exists():
                closed_day = ClosedDay.objects.get(date=appointment_date_obj)
                reason_text = f" ({closed_day.reason})" if closed_day.reason else ""
                messages.error(request, f'The clinic is closed on {appointment_date_obj.strftime("%B %d, %Y")}{reason_text}. Please select another date.')
                context = {
                    'service': service,
                    'attendants': get_available_attendants(),
                    'selected_date': appointment_date,
                    'selected_time': appointment_time,
                }
                return render(request, 'appointments/book_service.html', context)
            
            # Get the attendant - handle empty or invalid IDs
            available_attendants = get_available_attendants(selected_date=appointment_date, selected_time=appointment_time)
            if attendant_id:
                try:
                    attendant = User.objects.get(id=int(attendant_id), user_type='attendant')
                    # Verify that the attendant is active
                    if not attendant.is_active:
                        messages.error(request, 'This attendant account is currently inactive. Please select another attendant.')
                        context = {
                            'service': service,
                            'attendants': available_attendants,
                            'selected_date': appointment_date,
                            'selected_time': appointment_time,
                        }
                        return render(request, 'appointments/book_service.html', context)
                    # Check if attendant is in available list
                    if attendant not in available_attendants:
                        messages.error(request, 'This attendant is not available. Please select another attendant.')
                        context = {
                            'service': service,
                            'attendants': available_attendants,
                            'selected_date': appointment_date,
                            'selected_time': appointment_time,
                        }
                        return render(request, 'appointments/book_service.html', context)
                except (User.DoesNotExist, ValueError, TypeError):
                    # If attendant doesn't exist, get the first available attendant
                    if available_attendants.exists():
                        attendant = available_attendants.first()
                    else:
                        messages.error(request, 'No attendants available. Please contact the clinic.')
                        context = {
                            'service': service,
                            'attendants': available_attendants,
                            'selected_date': appointment_date,
                            'selected_time': appointment_time,
                        }
                        return render(request, 'appointments/book_service.html', context)
            else:
                # If no attendant selected, get the first available
                if available_attendants.exists():
                    attendant = available_attendants.first()
                else:
                    messages.error(request, 'No attendants available. Please contact the clinic.')
                    context = {
                        'service': service,
                        'attendants': available_attendants,
                        'selected_date': appointment_date,
                        'selected_time': appointment_time,
                    }
                    return render(request, 'appointments/book_service.html', context)
            
            # Check attendant availability based on work schedule
            appointment_datetime = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")
            day_name = appointment_datetime.strftime('%A')
            appointment_time_obj = datetime.strptime(appointment_time, "%H:%M").time()
            
            # Policy: Patients cannot book 45 minutes before closing (5:15 PM+). Clinic closes at 6:00 PM.
            cutoff_before_closing = datetime.strptime('17:15', '%H:%M').time()  # 45 minutes before 6:00 PM
            if appointment_time_obj >= cutoff_before_closing:
                messages.error(request, 'Booking is not allowed within 45 minutes of closing time. The last available booking time is 5:15 PM.')
                context = {
                    'service': service,
                    'attendants': available_attendants,
                    'selected_date': appointment_date,
                    'selected_time': appointment_time,
                }
                return render(request, 'appointments/book_service.html', context)
            
            # Check if same-day booking is at least 30 minutes in advance
            appointment_date_obj_temp = datetime.strptime(appointment_date, "%Y-%m-%d").date()
            if appointment_date_obj_temp == timezone.now().date():  # Same day booking
                appointment_datetime_aware = timezone.make_aware(appointment_datetime)
                time_until_appointment = appointment_datetime_aware - timezone.now()
                if time_until_appointment.total_seconds() < 30 * 60:  # Less than 30 minutes
                    messages.error(request, 'Same-day appointments must be booked at least 30 minutes in advance.')
                    context = {
                        'service': service,
                        'attendants': available_attendants,
                        'selected_date': appointment_date,
                        'selected_time': appointment_time,
                    }
                    return render(request, 'appointments/book_service.html', context)
            
            # Check if attendant has a profile and is active
            attendant_available = True
            profile = getattr(attendant, 'attendant_profile', None)
            
            if profile:
                # Check if work days are set
                if not profile.work_days or len(profile.work_days) == 0:
                    messages.error(request, f'{attendant.first_name} {attendant.last_name} has no work days configured. Please contact the clinic or select another attendant.')
                    context = {
                        'service': service,
                        'attendants': available_attendants,
                        'selected_date': appointment_date,
                        'selected_time': appointment_time,
                    }
                    return render(request, 'appointments/book_service.html', context)
                
                # Check if it's a work day
                if day_name not in profile.work_days:
                    messages.error(request, f'{attendant.first_name} {attendant.last_name} is not available on {day_name}. Please choose another day or attendant.')
                    context = {
                        'service': service,
                        'attendants': available_attendants,
                        'selected_date': appointment_date,
                        'selected_time': appointment_time,
                    }
                    return render(request, 'appointments/book_service.html', context)
                
                # Check if time is within work hours (allow booking AT end_time, reject AFTER end_time)
                if appointment_time_obj < profile.start_time or appointment_time_obj > profile.end_time:
                    messages.error(request, f'Appointment time must be between {profile.start_time.strftime("%I:%M %p")} and {profile.end_time.strftime("%I:%M %p")} for {attendant.first_name} {attendant.last_name}.')
                    context = {
                        'service': service,
                        'attendants': available_attendants,
                        'selected_date': appointment_date,
                        'selected_time': appointment_time,
                    }
                    return render(request, 'appointments/book_service.html', context)
                attendant_available = True
            else:
                # If no profile exists, reject the booking
                messages.error(request, f'{attendant.first_name} {attendant.last_name} has no work schedule configured. Please contact the clinic or select another attendant.')
                context = {
                    'service': service,
                    'attendants': available_attendants,
                    'selected_date': appointment_date,
                    'selected_time': appointment_time,
                }
                return render(request, 'appointments/book_service.html', context)
            
            # Check for existing appointments at the same time slot
            existing_appointments = Appointment.objects.filter(
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                attendant=attendant,
                status__in=['scheduled', 'confirmed']
            ).count()
            
            # Maximum 1 patient per time slot
            if existing_appointments >= 1:
                messages.error(request, f'This time slot ({appointment_time}) on {appointment_date} is already fully booked. Please choose another time.')
                context = {
                    'service': service,
                    'attendants': available_attendants,
                    'selected_date': appointment_date,
                    'selected_time': appointment_time,
                }
                return render(request, 'appointments/book_service.html', context)
            
            # Check for 1-hour gap requirement (attendant rest and preparation time)
            from datetime import timedelta
            appointment_datetime = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")
            one_hour_before = (appointment_datetime - timedelta(hours=1)).time()
            one_hour_after = (appointment_datetime + timedelta(hours=1)).time()
            
            # Check if there's an appointment within 1 hour before or after
            conflicting_appointments = Appointment.objects.filter(
                appointment_date=appointment_date,
                attendant=attendant,
                status__in=['scheduled', 'confirmed', 'completed']
            ).exclude(appointment_time=appointment_time)
            
            for existing_apt in conflicting_appointments:
                existing_time = datetime.strptime(str(existing_apt.appointment_time), "%H:%M:%S").time()
                time_diff_minutes = abs((datetime.combine(datetime.min, appointment_time_obj) - datetime.combine(datetime.min, existing_time)).total_seconds() / 60)
                
                if time_diff_minutes < 60:  # Less than 1 hour gap
                    messages.error(request, f'This time slot is too close to another appointment. Attendants require at least 1 hour between appointments for rest and preparation. Please select a time at least 1 hour away from {existing_time.strftime("%I:%M %p")}.')
                    context = {
                        'service': service,
                        'attendants': available_attendants,
                        'selected_date': appointment_date,
                        'selected_time': appointment_time,
                    }
                    return render(request, 'appointments/book_service.html', context)
            
            # Handle room selection
            from .models import Room
            available_rooms = Room.objects.filter(is_available=True)
            
            if room_id:
                try:
                    room = Room.objects.get(id=int(room_id), is_available=True)
                except (Room.DoesNotExist, ValueError, TypeError):
                    # If room doesn't exist or is unavailable, get the first available room
                    if available_rooms.exists():
                        room = available_rooms.first()
                    else:
                        messages.error(request, 'No rooms available. Please contact the clinic.')
                        context = {
                            'service': service,
                            'attendants': available_attendants,
                            'rooms': available_rooms,
                            'selected_date': appointment_date,
                            'selected_time': appointment_time,
                        }
                        return render(request, 'appointments/book_service.html', context)
            else:
                # If no room selected, get the first available
                if available_rooms.exists():
                    room = available_rooms.first()
                else:
                    messages.error(request, 'No rooms available. Please contact the clinic.')
                    context = {
                        'service': service,
                        'attendants': available_attendants,
                        'rooms': available_rooms,
                        'selected_date': appointment_date,
                        'selected_time': appointment_time,
                    }
                    return render(request, 'appointments/book_service.html', context)
            
            # Check if room is already booked at this time
            room_conflicts = Appointment.objects.filter(
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                room=room,
                status__in=['scheduled', 'confirmed']
            ).count()
            
            if room_conflicts >= 1:
                messages.error(request, f'Room {room.name} is already booked at this time. Please select another room or time.')
                context = {
                    'service': service,
                    'attendants': available_attendants,
                    'rooms': available_rooms,
                    'selected_date': appointment_date,
                    'selected_time': appointment_time,
                }
                return render(request, 'appointments/book_service.html', context)
            
            # Generate transaction ID
            import uuid
            transaction_id = str(uuid.uuid4())[:8].upper()
            
            # All appointments start as scheduled and require staff confirmation
            initial_status = 'scheduled'
            
            appointment = Appointment.objects.create(
                patient=request.user,
                service=service,
                attendant=attendant,
                room=room,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status=initial_status,
                transaction_id=transaction_id
            )
            
            # Log appointment booking
            from .models import HistoryLog
            HistoryLog.objects.create(
                action_type='book',
                item_type='appointment',
                item_id=appointment.id,
                item_name=f"{service.service_name} - {request.user.get_full_name()}",
                performed_by=request.user,
                details={
                    'appointment_id': appointment.id,
                    'patient': request.user.get_full_name(),
                    'service': service.service_name,
                    'attendant': f"{attendant.first_name} {attendant.last_name}",
                    'date': str(appointment_date),
                    'time': str(appointment_time),
                    'status': initial_status,
                    'transaction_id': transaction_id,
                }
            )
            
            # Create notification for patient
            Notification.objects.create(
                type='appointment',
                appointment_id=appointment.id,
                title='Appointment Scheduled',
                message=f'Your {service.service_name} appointment has been scheduled for {appointment_date} at {appointment_time}. Please await staff confirmation. Transaction ID: {transaction_id}',
                patient=request.user
            )
            
            # Notify staff of new appointment booking
            Notification.objects.create(
                type='appointment',
                appointment_id=appointment.id,
                title='New Appointment Booked',
                message=f'New appointment booked: {appointment.patient.get_full_name()} - {appointment.get_service_name()} on {appointment.appointment_date} at {appointment.appointment_time}. Status: {appointment.status}. Please review and confirm.',
                patient=None  # Staff notification
            )
            
            # Send SMS to patient with scheduled confirmation (not final confirmation)
            sms_result = send_appointment_sms(appointment, 'scheduled')
            if sms_result['success']:
                messages.success(request, f'Appointment scheduled! Please await staff confirmation. Transaction ID: {transaction_id}')
            else:
                # SMS failed - check why and provide helpful message
                error_msg = sms_result.get('error', '')
                if 'phone number not available' in error_msg.lower() or 'phone' in error_msg.lower():
                    messages.warning(request, f'Appointment scheduled! Please await staff confirmation. Note: SMS notification could not be sent - please ensure your phone number is set in your profile. Transaction ID: {transaction_id}')
                else:
                    messages.success(request, f'Appointment scheduled! Please await staff confirmation. Transaction ID: {transaction_id}')
            
            # Send SMS and create in-app notification for attendant
            try:
                if attendant and attendant.is_active:
                    # Send SMS to attendant
                    send_attendant_assignment_sms(appointment)
                    
                    # Create in-app notification for attendant
                    Notification.objects.create(
                        type='appointment',
                        appointment_id=appointment.id,
                        title='New Appointment Assigned',
                        message=f'You have been assigned a new appointment: {appointment.patient.get_full_name()} - {appointment.get_service_name()} on {appointment.appointment_date} at {appointment.appointment_time}.',
                        patient=attendant  # Store attendant user in patient field for notification
                    )
            except Exception as e:
                # Log error but don't fail the booking
                pass
            
            return redirect('appointments:my_appointments')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    # Get available attendants based on selected date/time (if provided)
    selected_date = request.GET.get('date', '')
    selected_time = request.GET.get('time', '')
    available_attendants = get_available_attendants(selected_date, selected_time)
    
    # Get closed days for calendar display
    closed_days = ClosedDay.objects.all().values_list('date', flat=True)
    closed_days_list = [str(date) for date in closed_days]
    closed_days_json = json.dumps(closed_days_list)
    
    # Get active time slots from database
    from .models import TimeSlot
    time_slots = TimeSlot.objects.filter(is_active=True).order_by('time')
    time_slots_list = [
        {
            'value': slot.time.strftime('%H:%M'),
            'display': slot.time.strftime('%I:%M %p')
        }
        for slot in time_slots
    ]
    time_slots_json = json.dumps(time_slots_list)
    
    # Get booked appointments grouped by date for calendar display
    from django.db.models import Q
    booked_appointments = Appointment.objects.filter(
        Q(status='scheduled') | Q(status='confirmed')
    ).values('appointment_date', 'appointment_time')
    
    # Group booked appointments by date
    booked_slots = {}
    for appt in booked_appointments:
        date_str = str(appt['appointment_date'])
        time_str = appt['appointment_time'].strftime('%H:%M')
        if date_str not in booked_slots:
            booked_slots[date_str] = []
        booked_slots[date_str].append(time_str)
    
    booked_slots_json = json.dumps(booked_slots)
    
    # Get available rooms
    from .models import Room
    rooms = Room.objects.filter(is_available=True).order_by('name')
    
    context = {
        'service': service,
        'attendants': available_attendants,
        'rooms': rooms,
        'selected_date': selected_date,
        'selected_time': selected_time,
        'closed_days': closed_days_json,
        'time_slots': time_slots_json,
        'booked_slots': booked_slots_json,  # Add booked slots data
    }
    
    return render(request, 'appointments/book_service.html', context)


@login_required
def book_product(request, product_id):
    """Book a product order"""
    product = get_object_or_404(Product, id=product_id)
    
    # Check if product is out of stock - redirect to products page with error message
    if product.stock <= 0:
        messages.error(request, f'Sorry, {product.product_name} is currently out of stock. Please choose another product or check back later.')
        return redirect('products:list')
    
    if request.method == 'POST':
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        quantity = int(request.POST.get('quantity', 1))
        
        if appointment_date and appointment_time:
            # Validate quantity
            if quantity < 1:
                messages.error(request, 'Quantity must be at least 1.')
                context = {
                    'product': product,
                }
                return render(request, 'appointments/book_product.html', context)
            
            if quantity > product.stock:
                messages.error(request, f'Quantity ({quantity}) cannot exceed available stock ({product.stock} units).')
                context = {
                    'product': product,
                }
                return render(request, 'appointments/book_product.html', context)
            # Validate that date and time are not in the past
            from django.utils import timezone
            appointment_datetime_str = f"{appointment_date} {appointment_time}"
            try:
                appointment_datetime = datetime.strptime(appointment_datetime_str, "%Y-%m-%d %H:%M")
                appointment_datetime_aware = timezone.make_aware(appointment_datetime)
                
                if appointment_datetime_aware <= timezone.now():
                    messages.error(request, 'Cannot book appointments in the past. Time has already passed. Please select a future date and time.')
                    context = {
                        'product': product,
                    }
                    return render(request, 'appointments/book_product.html', context)
            except ValueError:
                messages.error(request, 'Invalid date or time format.')
                context = {
                    'product': product,
                }
                return render(request, 'appointments/book_product.html', context)
            
            # Check if the selected date is a closed clinic day
            appointment_date_obj = datetime.strptime(appointment_date, "%Y-%m-%d").date()
            if ClosedDay.objects.filter(date=appointment_date_obj).exists():
                closed_day = ClosedDay.objects.get(date=appointment_date_obj)
                reason_text = f" ({closed_day.reason})" if closed_day.reason else ""
                messages.error(request, f'The clinic is closed on {appointment_date_obj.strftime("%B %d, %Y")}{reason_text}. Please select another date.')
                context = {
                    'product': product,
                }
                return render(request, 'appointments/book_product.html', context)
            
            # Check for existing appointments at the same time slot
            # For products, we still want to prevent double-booking the same time slot
            existing_appointments = Appointment.objects.filter(
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status__in=['scheduled', 'confirmed']
            ).count()
            
            # Maximum 1 patient per time slot
            if existing_appointments >= 1:
                messages.error(request, f'This time slot ({appointment_time}) on {appointment_date} is already fully booked. Please choose another time.')
                context = {
                    'product': product,
                }
                return render(request, 'appointments/book_product.html', context)
            
            # Check for 1-hour gap requirement (attendant rest and preparation time)
            from datetime import timedelta
            appointment_datetime = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")
            appointment_time_obj = datetime.strptime(appointment_time, "%H:%M").time()
            
            # Check if there's an appointment within 1 hour before or after
            conflicting_appointments = Appointment.objects.filter(
                appointment_date=appointment_date,
                attendant=attendant,
                status__in=['scheduled', 'confirmed', 'completed']
            ).exclude(appointment_time=appointment_time)
            
            for existing_apt in conflicting_appointments:
                existing_time = datetime.strptime(str(existing_apt.appointment_time), "%H:%M:%S").time()
                time_diff_minutes = abs((datetime.combine(datetime.min, appointment_time_obj) - datetime.combine(datetime.min, existing_time)).total_seconds() / 60)
                
                if time_diff_minutes < 60:  # Less than 1 hour gap
                    messages.error(request, f'This time slot is too close to another appointment. Attendants require at least 1 hour between appointments for rest and preparation. Please select a time at least 1 hour away from {existing_time.strftime("%I:%M %p")}.')
                    context = {
                        'product': product,
                    }
                    return render(request, 'appointments/book_product.html', context)
            
            # Check stock availability
            if product.stock <= 0:
                messages.error(request, f'Sorry, {product.product_name} is currently out of stock. Please check back later or contact the clinic.')
                context = {
                    'product': product,
                }
                return render(request, 'appointments/book_product.html', context)
            
            # Policy: Patients cannot book 45 minutes before closing (5:15 PM+). Clinic closes at 6:00 PM.
            appointment_time_obj = datetime.strptime(appointment_time, "%H:%M").time()
            cutoff_before_closing = datetime.strptime('17:15', '%H:%M').time()  # 45 minutes before 6:00 PM
            if appointment_time_obj >= cutoff_before_closing:
                messages.error(request, 'Booking is not allowed within 45 minutes of closing time. The last available booking time is 5:15 PM.')
                context = {
                    'product': product,
                }
                return render(request, 'appointments/book_product.html', context)
            
            # Check if same-day booking is at least 30 minutes in advance
            appointment_date_obj = datetime.strptime(appointment_date, "%Y-%m-%d").date()
            if appointment_date_obj == timezone.now().date():  # Same day booking
                appointment_datetime = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")
                appointment_datetime_aware = timezone.make_aware(appointment_datetime)
                time_until_appointment = appointment_datetime_aware - timezone.now()
                if time_until_appointment.total_seconds() < 30 * 60:  # Less than 30 minutes
                    messages.error(request, 'Same-day appointments must be booked at least 30 minutes in advance.')
                    context = {
                        'product': product,
                    }
                    return render(request, 'appointments/book_product.html', context)
            
            # Get the default attendant for product orders (first active attendant user)
            attendant = User.objects.filter(user_type='attendant', is_active=True).first()
            if not attendant:
                messages.error(request, 'No attendants available. Please contact the clinic.')
                context = {
                    'product': product,
                }
                return render(request, 'appointments/book_product.html', context)
            
            # Generate transaction ID
            import uuid
            transaction_id = str(uuid.uuid4())[:8].upper()
            
            # All appointments start as scheduled and require staff confirmation
            initial_status = 'scheduled'
            
            appointment = Appointment.objects.create(
                patient=request.user,
                product=product,
                attendant=attendant,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                quantity=quantity,
                status=initial_status,
                transaction_id=transaction_id
            )
            
            # Log product order booking
            from .models import HistoryLog
            total_amount = product.price * quantity
            HistoryLog.objects.create(
                action_type='book',
                item_type='appointment',
                item_id=appointment.id,
                item_name=f"{product.product_name} (x{quantity}) - {request.user.get_full_name()}",
                performed_by=request.user,
                details={
                    'appointment_id': appointment.id,
                    'patient': request.user.get_full_name(),
                    'product': product.product_name,
                    'quantity': quantity,
                    'unit_price': str(product.price),
                    'total_amount': str(total_amount),
                    'attendant': f"{attendant.first_name} {attendant.last_name}",
                    'date': str(appointment_date),
                    'time': str(appointment_time),
                    'status': initial_status,
                    'transaction_id': transaction_id,
                }
            )
            
            # Deduct stock only when staff confirms the order
            # Stock will be deducted when appointment status changes to 'confirmed'
            
            # Create notification for patient
            Notification.objects.create(
                type='appointment',
                appointment_id=appointment.id,
                title='Product Order Scheduled',
                message=f'Your order for {quantity}x {product.product_name} has been scheduled for pickup on {appointment_date} at {appointment_time}. Total: ₱{total_amount:.2f}. Please await staff confirmation. Transaction ID: {transaction_id}',
                patient=request.user
            )
            
            # Notify staff of product order
            Notification.objects.create(
                type='appointment',
                appointment_id=appointment.id,
                title='Product Order',
                message=f'Product order: {request.user.get_full_name()} - {quantity}x {product.product_name} (₱{total_amount:.2f}) on {appointment_date} at {appointment_time}. Status: {initial_status}. Please review and confirm.',
                patient=None  # Staff notification
            )
            
            # Send SMS to patient with scheduled confirmation
            sms_result = send_appointment_sms(appointment, 'scheduled')
            if sms_result['success']:
                messages.success(request, f'Product ordered successfully! Please await staff confirmation. Transaction ID: {transaction_id}')
            else:
                # SMS failed - check why and provide helpful message
                error_msg = sms_result.get('error', '')
                if 'phone number not available' in error_msg.lower() or 'phone' in error_msg.lower():
                    messages.warning(request, f'Product ordered successfully! Please await staff confirmation. Note: SMS notification could not be sent - please ensure your phone number is set in your profile. Transaction ID: {transaction_id}')
                else:
                    messages.success(request, f'Product ordered successfully! Please await staff confirmation. Transaction ID: {transaction_id}')
            return redirect('appointments:my_appointments')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    # Get closed days for calendar display
    closed_days = ClosedDay.objects.all().values_list('date', flat=True)
    closed_days_list = [str(date) for date in closed_days]
    closed_days_json = json.dumps(closed_days_list)
    
    # Get active time slots from database
    from .models import TimeSlot
    time_slots = TimeSlot.objects.filter(is_active=True).order_by('time')
    time_slots_list = [
        {
            'value': slot.time.strftime('%H:%M'),
            'display': slot.time.strftime('%I:%M %p')
        }
        for slot in time_slots
    ]
    time_slots_json = json.dumps(time_slots_list)
    
    # Get booked appointments grouped by date for calendar display
    from django.db.models import Q
    booked_appointments = Appointment.objects.filter(
        Q(status='scheduled') | Q(status='confirmed')
    ).values('appointment_date', 'appointment_time')
    
    # Group booked appointments by date
    booked_slots = {}
    for appt in booked_appointments:
        date_str = str(appt['appointment_date'])
        time_str = appt['appointment_time'].strftime('%H:%M')
        if date_str not in booked_slots:
            booked_slots[date_str] = []
        booked_slots[date_str].append(time_str)
    
    booked_slots_json = json.dumps(booked_slots)
    
    context = {
        'product': product,
        'closed_days': closed_days_json,
        'time_slots': time_slots_json,
        'booked_slots': booked_slots_json,  # Add booked slots data
    }
    
    return render(request, 'appointments/book_product.html', context)


@login_required
def book_package(request, package_id):
    """Book a package"""
    package = get_object_or_404(Package, id=package_id)
    
    if request.method == 'POST':
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        attendant_id = request.POST.get('attendant', '')
        
        if appointment_date and appointment_time:
            # Validate that date and time are not in the past
            from django.utils import timezone
            appointment_datetime_str = f"{appointment_date} {appointment_time}"
            try:
                appointment_datetime = datetime.strptime(appointment_datetime_str, "%Y-%m-%d %H:%M")
                appointment_datetime_aware = timezone.make_aware(appointment_datetime)
                
                if appointment_datetime_aware <= timezone.now():
                    messages.error(request, 'Cannot book appointments in the past. Time has already passed. Please select a future date and time.')
                    context = {
                        'package': package,
                        'attendants': get_available_attendants(),
                    }
                    return render(request, 'appointments/book_package.html', context)
            except ValueError:
                messages.error(request, 'Invalid date or time format.')
                context = {
                    'package': package,
                    'attendants': get_available_attendants(),
                }
                return render(request, 'appointments/book_package.html', context)
            
            # Check if the selected date is a closed clinic day
            appointment_date_obj = datetime.strptime(appointment_date, "%Y-%m-%d").date()
            if ClosedDay.objects.filter(date=appointment_date_obj).exists():
                closed_day = ClosedDay.objects.get(date=appointment_date_obj)
                reason_text = f" ({closed_day.reason})" if closed_day.reason else ""
                messages.error(request, f'The clinic is closed on {appointment_date_obj.strftime("%B %d, %Y")}{reason_text}. Please select another date.')
                context = {
                    'package': package,
                    'attendants': get_available_attendants(),
                    'selected_date': appointment_date,
                    'selected_time': appointment_time,
                }
                return render(request, 'appointments/book_package.html', context)
            
            # Get the attendant - handle empty or invalid IDs
            available_attendants = get_available_attendants(selected_date=appointment_date, selected_time=appointment_time)
            if attendant_id:
                try:
                    attendant = User.objects.get(id=int(attendant_id), user_type='attendant')
                    # Verify that the attendant is active
                    if not attendant.is_active:
                        messages.error(request, 'This attendant account is currently inactive. Please select another attendant.')
                        context = {
                            'package': package,
                            'attendants': available_attendants,
                            'selected_date': appointment_date,
                            'selected_time': appointment_time,
                        }
                        return render(request, 'appointments/book_package.html', context)
                    # Check if attendant is in available list
                    if attendant not in available_attendants:
                        messages.error(request, 'This attendant is not available. Please select another attendant.')
                        context = {
                            'package': package,
                            'attendants': available_attendants,
                            'selected_date': appointment_date,
                            'selected_time': appointment_time,
                        }
                        return render(request, 'appointments/book_package.html', context)
                except (User.DoesNotExist, ValueError, TypeError):
                    # If attendant doesn't exist, get the first available attendant
                    if available_attendants.exists():
                        attendant = available_attendants.first()
                    else:
                        messages.error(request, 'No attendants available. Please contact the clinic.')
                        context = {
                            'package': package,
                            'attendants': available_attendants,
                            'selected_date': appointment_date,
                            'selected_time': appointment_time,
                        }
                        return render(request, 'appointments/book_package.html', context)
            else:
                # If no attendant selected, get the first available
                if available_attendants.exists():
                    attendant = available_attendants.first()
                else:
                    messages.error(request, 'No attendants available. Please contact the clinic.')
                    context = {
                        'package': package,
                        'attendants': available_attendants,
                        'selected_date': appointment_date,
                        'selected_time': appointment_time,
                    }
                    return render(request, 'appointments/book_package.html', context)
            
            # Check attendant availability based on work schedule
            appointment_datetime = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")
            day_name = appointment_datetime.strftime('%A')
            appointment_time_obj = datetime.strptime(appointment_time, "%H:%M").time()
            
            # Policy: Patients cannot book 45 minutes before closing (5:15 PM+). Clinic closes at 6:00 PM.
            cutoff_before_closing = datetime.strptime('17:15', '%H:%M').time()  # 45 minutes before 6:00 PM
            if appointment_time_obj >= cutoff_before_closing:
                messages.error(request, 'Booking is not allowed within 45 minutes of closing time. The last available booking time is 5:15 PM.')
                context = {
                    'package': package,
                    'attendants': available_attendants,
                    'selected_date': appointment_date,
                    'selected_time': appointment_time,
                }
                return render(request, 'appointments/book_package.html', context)
            
            # Check if same-day booking is at least 30 minutes in advance
            appointment_date_obj_temp = datetime.strptime(appointment_date, "%Y-%m-%d").date()
            if appointment_date_obj_temp == timezone.now().date():  # Same day booking
                appointment_datetime_aware = timezone.make_aware(appointment_datetime)
                time_until_appointment = appointment_datetime_aware - timezone.now()
                if time_until_appointment.total_seconds() < 30 * 60:  # Less than 30 minutes
                    messages.error(request, 'Same-day appointments must be booked at least 30 minutes in advance.')
                    context = {
                        'package': package,
                        'attendants': available_attendants,
                        'selected_date': appointment_date,
                        'selected_time': appointment_time,
                    }
                    return render(request, 'appointments/book_package.html', context)
            
            # Check if attendant has a profile and is active
            profile = getattr(attendant, 'attendant_profile', None)
            
            if profile:
                # Check if work days are set
                if not profile.work_days or len(profile.work_days) == 0:
                    messages.error(request, f'{attendant.first_name} {attendant.last_name} has no work days configured. Please contact the clinic or select another attendant.')
                    context = {
                        'package': package,
                        'attendants': available_attendants,
                        'selected_date': appointment_date,
                        'selected_time': appointment_time,
                    }
                    return render(request, 'appointments/book_package.html', context)
                
                # Check if it's a work day
                if day_name not in profile.work_days:
                    messages.error(request, f'{attendant.first_name} {attendant.last_name} is not available on {day_name}. Please choose another day or attendant.')
                    context = {
                        'package': package,
                        'attendants': available_attendants,
                        'selected_date': appointment_date,
                        'selected_time': appointment_time,
                    }
                    return render(request, 'appointments/book_package.html', context)
                
                # Check if time is within work hours (allow booking AT end_time, reject AFTER end_time)
                if appointment_time_obj < profile.start_time or appointment_time_obj > profile.end_time:
                    messages.error(request, f'Appointment time must be between {profile.start_time.strftime("%I:%M %p")} and {profile.end_time.strftime("%I:%M %p")} for {attendant.first_name} {attendant.last_name}.')
                    context = {
                        'package': package,
                        'attendants': available_attendants,
                        'selected_date': appointment_date,
                        'selected_time': appointment_time,
                    }
                    return render(request, 'appointments/book_package.html', context)
            else:
                # If no profile exists, reject the booking
                messages.error(request, f'{attendant.first_name} {attendant.last_name} has no work schedule configured. Please contact the clinic or select another attendant.')
                context = {
                    'package': package,
                    'attendants': available_attendants,
                    'selected_date': appointment_date,
                    'selected_time': appointment_time,
                }
                return render(request, 'appointments/book_package.html', context)
            
            # Check for existing appointments at the same time slot
            existing_appointments = Appointment.objects.filter(
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                attendant=attendant,
                status__in=['scheduled', 'confirmed']
            ).count()
            
            # Maximum 1 patient per time slot
            if existing_appointments >= 1:
                messages.error(request, f'This time slot ({appointment_time}) on {appointment_date} is already fully booked. Please choose another time.')
                context = {
                    'package': package,
                    'attendants': available_attendants,
                    'selected_date': appointment_date,
                    'selected_time': appointment_time,
                }
                return render(request, 'appointments/book_package.html', context)
            
            # Check for 1-hour gap requirement (attendant rest and preparation time)
            from datetime import timedelta
            appointment_datetime = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")
            one_hour_before = (appointment_datetime - timedelta(hours=1)).time()
            one_hour_after = (appointment_datetime + timedelta(hours=1)).time()
            
            # Check if there's an appointment within 1 hour before or after
            conflicting_appointments = Appointment.objects.filter(
                appointment_date=appointment_date,
                attendant=attendant,
                status__in=['scheduled', 'confirmed', 'completed']
            ).exclude(appointment_time=appointment_time)
            
            for existing_apt in conflicting_appointments:
                existing_time = datetime.strptime(str(existing_apt.appointment_time), "%H:%M:%S").time()
                time_diff_minutes = abs((datetime.combine(datetime.min, appointment_time_obj) - datetime.combine(datetime.min, existing_time)).total_seconds() / 60)
                
                if time_diff_minutes < 60:  # Less than 1 hour gap
                    messages.error(request, f'This time slot is too close to another appointment. Attendants require at least 1 hour between appointments for rest and preparation. Please select a time at least 1 hour away from {existing_time.strftime("%I:%M %p")}.')
                    context = {
                        'package': package,
                        'attendants': available_attendants,
                        'selected_date': appointment_date,
                        'selected_time': appointment_time,
                    }
                    return render(request, 'appointments/book_package.html', context)
            
            # Generate transaction ID
            import uuid
            transaction_id = str(uuid.uuid4())[:8].upper()
            
            # All appointments start as scheduled and require staff approval
            initial_status = 'scheduled'
            
            appointment = Appointment.objects.create(
                patient=request.user,
                package=package,
                attendant=attendant,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status=initial_status,
                transaction_id=transaction_id
            )
            
            # Log package booking
            from .models import HistoryLog
            HistoryLog.objects.create(
                action_type='book',
                item_type='appointment',
                item_id=appointment.id,
                item_name=f"{package.package_name} - {request.user.get_full_name()}",
                performed_by=request.user,
                details={
                    'appointment_id': appointment.id,
                    'patient': request.user.get_full_name(),
                    'package': package.package_name,
                    'attendant': f"{attendant.first_name} {attendant.last_name}",
                    'date': str(appointment_date),
                    'time': str(appointment_time),
                    'status': initial_status,
                    'transaction_id': transaction_id,
                }
            )
            
            # Create notification
            Notification.objects.create(
                type='appointment',
                appointment_id=appointment.id,
                title='Package Booked',
                message=f'Your {package.package_name} package has been booked for {appointment_date} at {appointment_time}. Waiting for staff approval. Transaction ID: {transaction_id}',
                patient=request.user
            )
            
            # Notify owner of package booking (single notification for all owners)
            Notification.objects.create(
                type='appointment',
                appointment_id=appointment.id,
                title='Package Booked',
                message=f'Package booking: {request.user.get_full_name()} - {package.package_name} on {appointment_date} at {appointment_time}. Status: {initial_status}.',
                patient=None  # Owner notification
            )
            
            messages.success(request, f'Package booked! Waiting for staff approval. Transaction ID: {transaction_id}')
            return redirect('appointments:my_appointments')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    # Get available attendants based on selected date/time (if provided)
    selected_date = request.GET.get('date', '')
    selected_time = request.GET.get('time', '')
    available_attendants = get_available_attendants(selected_date, selected_time)
    
    # Get closed days for calendar display
    closed_days = ClosedDay.objects.all().values_list('date', flat=True)
    closed_days_list = [str(date) for date in closed_days]
    closed_days_json = json.dumps(closed_days_list)
    
    # Get active time slots from database
    from .models import TimeSlot
    time_slots = TimeSlot.objects.filter(is_active=True).order_by('time')
    time_slots_list = [
        {
            'value': slot.time.strftime('%H:%M'),
            'display': slot.time.strftime('%I:%M %p')
        }
        for slot in time_slots
    ]
    time_slots_json = json.dumps(time_slots_list)
    
    # Get booked appointments grouped by date for calendar display
    from django.db.models import Q
    booked_appointments = Appointment.objects.filter(
        Q(status='scheduled') | Q(status='confirmed')
    ).values('appointment_date', 'appointment_time')
    
    # Group booked appointments by date
    booked_slots = {}
    for appt in booked_appointments:
        date_str = str(appt['appointment_date'])
        time_str = appt['appointment_time'].strftime('%H:%M')
        if date_str not in booked_slots:
            booked_slots[date_str] = []
        booked_slots[date_str].append(time_str)
    
    booked_slots_json = json.dumps(booked_slots)
    
    context = {
        'package': package,
        'attendants': available_attendants,
        'selected_date': selected_date,
        'selected_time': selected_time,
        'closed_days': closed_days_json,
        'time_slots': time_slots_json,
        'booked_slots': booked_slots_json,  # Add booked slots data
    }
    
    return render(request, 'appointments/book_package.html', context)


@login_required
def notifications(request):
    """User's notifications"""
    notifications = Notification.objects.filter(patient=request.user).order_by('-created_at')
    
    # Mark notifications as read
    notifications.update(is_read=True)
    
    context = {
        'notifications': notifications,
    }
    
    return render(request, 'appointments/notifications.html', context)


@login_required
def request_cancellation(request, appointment_id):
    """Request cancellation for an appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)
    
    # Check if appointment can be cancelled (must be at least 2 days before)
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    appointment_datetime = timezone.make_aware(
        datetime.combine(appointment.appointment_date, appointment.appointment_time)
    )
    days_until_appointment = (appointment_datetime - timezone.now()).days
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Require cancellation reason
        if not reason:
            if is_ajax:
                return JsonResponse({'success': False, 'message': 'Cancellation reason is required. Please provide a reason for cancelling.'}, status=400)
            messages.error(request, 'Cancellation reason is required. Please provide a reason for cancelling.')
            return redirect('appointments:my_appointments')
        
        # Check if appointment can be cancelled
        if appointment.status not in ['pending', 'confirmed']:
            if is_ajax:
                return JsonResponse({'success': False, 'message': 'This appointment cannot be cancelled.'}, status=400)
            messages.error(request, 'This appointment cannot be cancelled.')
            return redirect('appointments:my_appointments')
        
        # Create cancellation request (for both within 2 days and more than 2 days)
        from .models import CancellationRequest
        
        # Determine appointment type
        appointment_type = 'regular'
        if appointment.package:
            appointment_type = 'package'
        
        # Check if cancellation request already exists
        cancellation_request = CancellationRequest.objects.filter(
            appointment_id=appointment.id,
            status='pending'
        ).first()
        
        if not cancellation_request:
            cancellation_request = CancellationRequest.objects.create(
                appointment_id=appointment.id,
                appointment_type=appointment_type,
                patient=request.user,
                reason=reason,
                status='pending'
            )
        
        # Notify owner of cancellation request (single notification for all owners)
        if days_until_appointment < 2:
            Notification.objects.create(
                type='cancellation',
                appointment_id=appointment.id,
                title='Cancellation Request (Within 2 Days)',
                message=f'Patient {request.user.full_name} has requested to cancel their appointment for {appointment.get_service_name()} on {appointment.appointment_date} at {appointment.appointment_time} within 2 days. Reason: {reason}. Please review.',
                patient=None  # Owner notification
            )
        else:
            Notification.objects.create(
                type='cancellation',
                appointment_id=appointment.id,
                title='Cancellation Request',
                message=f'Patient {request.user.full_name} has requested to cancel their appointment for {appointment.get_service_name()} on {appointment.appointment_date} at {appointment.appointment_time}. Reason: {reason}',
                patient=None  # Owner notification
            )
        
        # Redirect to appointments page
        if is_ajax:
            return JsonResponse({
                'success': True, 
                'message': 'Your cancellation request has been submitted. The clinic owner will review it shortly.',
                'redirect_url': '/appointments/my-appointments/'
            })
        messages.success(request, 'Your cancellation request has been submitted. The clinic owner will review it shortly.')
        return redirect('appointments:patient_appointments')
    
    # GET request - check if within 2 days
    if days_until_appointment < 2:
        messages.error(request, 'Cancellation is not allowed within 2 days of the appointment. The owner will be notified if you submit a request.')
        return redirect('appointments:my_appointments')
    
    # GET request - show cancellation form
    context = {
        'appointment': appointment,
        'days_until_appointment': days_until_appointment,
    }
    
    return render(request, 'appointments/request_cancellation.html', context)


@login_required
def handle_unavailable_attendant(request, appointment_id):
    """Patient handles unavailable attendant - choose from 3 options"""
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)
    
    # Check if there's a pending unavailability request
    from .models import AttendantUnavailabilityRequest
    try:
        unavailability_request = AttendantUnavailabilityRequest.objects.get(
            appointment=appointment,
            status='pending'
        )
    except AttendantUnavailabilityRequest.DoesNotExist:
        messages.error(request, 'No unavailability request found for this appointment.')
        return redirect('appointments:my_appointments')
    
    if request.method == 'POST':
        choice = request.POST.get('choice')
        
        # Record patient's choice
        unavailability_request.patient_choice = choice
        unavailability_request.status = 'resolved'
        unavailability_request.resolved_at = timezone.now()
        unavailability_request.save()
        
        # Create notification for owner
        Notification.objects.create(
            type='system',
            title='Patient Responded to Unavailability',
            message=f'Patient {appointment.patient.get_full_name()} chose: {dict(unavailability_request._meta.get_field("patient_choice").choices).get(choice, choice)} for appointment on {appointment.appointment_date}.'
        )
        
        if choice == 'choose_another':
            # Redirect to appointment booking with service/package/product to choose another attendant
            messages.info(request, 'Please select another available attendant for the same date and time.')
            if appointment.service:
                return redirect('appointments:book_service', service_id=appointment.service.id)
            elif appointment.package:
                return redirect('appointments:book_package', package_id=appointment.package.id)
            elif appointment.product:
                return redirect('appointments:book_product', product_id=appointment.product.id)
            else:
                messages.error(request, 'Unable to determine appointment type.')
                return redirect('appointments:my_appointments')
        
        elif choice == 'reschedule_same':
            # Redirect to reschedule request
            messages.info(request, 'Please select a new date and time with the same attendant.')
            return redirect('appointments:request_reschedule', appointment_id=appointment_id)
        
        elif choice == 'cancel':
            # Redirect to cancellation request
            messages.info(request, 'Please confirm cancellation of your appointment.')
            return redirect('appointments:request_cancellation', appointment_id=appointment_id)
        
        else:
            messages.error(request, 'Invalid choice. Please select one of the options.')
    
    context = {
        'appointment': appointment,
        'unavailability_request': unavailability_request,
    }
    
    return render(request, 'appointments/unavailable_attendant.html', context)


@login_required
def request_reschedule(request, appointment_id):
    """Request reschedule for an appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)
    
    # Check if this is from attendant unavailability workflow
    keep_attendant = request.GET.get('keep_attendant') == 'true'
    original_attendant = appointment.attendant if keep_attendant else None
    
    if request.method == 'POST':
        new_date = request.POST.get('new_appointment_date')
        new_time = request.POST.get('new_appointment_time')
        reason = request.POST.get('reason', '')
        
        if not new_date or not new_time:
            messages.error(request, 'Please provide both new date and time.')
            return redirect('appointments:request_reschedule', appointment_id=appointment_id)
        
        # Check if appointment can be rescheduled
        if appointment.status not in ['pending', 'confirmed']:
            messages.error(request, 'This appointment cannot be rescheduled.')
            return redirect('appointments:my_appointments')
        
        # Policy: Patients cannot reschedule when the appointment is within the same day
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        appointment_datetime = timezone.make_aware(
            datetime.combine(appointment.appointment_date, appointment.appointment_time)
        )
        current_datetime = timezone.now()
        days_until_appointment = (appointment_datetime.date() - current_datetime.date()).days
        
        if days_until_appointment < 1:
            messages.error(request, 'Rescheduling is not allowed when the appointment is within the same day. Please contact the clinic directly.')
            return redirect('appointments:my_appointments')
        
        # Validate that the new date/time is not in the past
        try:
            new_datetime = timezone.make_aware(
                datetime.combine(
                    datetime.strptime(new_date, '%Y-%m-%d').date(),
                    datetime.strptime(new_time, '%H:%M').time()
                )
            )
            
            if new_datetime <= current_datetime:
                messages.error(request, 'You cannot reschedule to a date and time in the past. Please select a future date and time.')
                return redirect('appointments:request_reschedule', appointment_id=appointment_id)
        except (ValueError, TypeError) as e:
            messages.error(request, 'Invalid date or time format. Please try again.')
            return redirect('appointments:request_reschedule', appointment_id=appointment_id)
        
        # Check if the new date is a closed clinic day
        new_date_obj = datetime.strptime(new_date, "%Y-%m-%d").date()
        if ClosedDay.objects.filter(date=new_date_obj).exists():
            closed_day = ClosedDay.objects.get(date=new_date_obj)
            reason_text = f" ({closed_day.reason})" if closed_day.reason else ""
            messages.error(request, f'The clinic is closed on {new_date_obj.strftime("%B %d, %Y")}{reason_text}. Please select another date.')
            return redirect('appointments:request_reschedule', appointment_id=appointment_id)
        
        # Create reschedule request
        from .models import RescheduleRequest
        
        reschedule_request = RescheduleRequest.objects.create(
            appointment_id=appointment.id,
            new_appointment_date=new_date,
            new_appointment_time=new_time,
            patient=request.user,
            reason=reason,
            status='pending'
        )
        
        # Create notification for staff
        Notification.objects.create(
            type='reschedule',
            appointment_id=appointment.id,
            title='Reschedule Request',
            message=f'Patient {request.user.full_name} has requested to reschedule their appointment for {appointment.get_service_name()} from {appointment.appointment_date} at {appointment.appointment_time} to {new_date} at {new_time}. Reason: {reason}',
            patient=None  # Staff notification
        )
        
        # Notify owner of reschedule request (single notification for all owners)
        Notification.objects.create(
            type='reschedule',
            appointment_id=appointment.id,
            title='Reschedule Request',
            message=f'Patient {request.user.full_name} has requested to reschedule their appointment for {appointment.get_service_name()} from {appointment.appointment_date} at {appointment.appointment_time} to {new_date} at {new_time}.',
            patient=None  # Owner notification
        )
        
        messages.success(request, 'Your reschedule request has been submitted. The staff will review it shortly.')
        return redirect('appointments:my_appointments')
    
    # GET request - check if rescheduling is allowed
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    appointment_datetime = timezone.make_aware(
        datetime.combine(appointment.appointment_date, appointment.appointment_time)
    )
    current_datetime = timezone.now()
    days_until_appointment = (appointment_datetime.date() - current_datetime.date()).days
    
    # Policy: Patients cannot reschedule when the appointment is within the same day
    if days_until_appointment < 1:
        messages.error(request, 'Rescheduling is not allowed when the appointment is within the same day. Please contact the clinic directly.')
        return redirect('appointments:my_appointments')
    
    # GET request - show reschedule form with calendar
    # Get closed days for calendar display
    closed_days = ClosedDay.objects.all().values_list('date', flat=True)
    closed_days_list = [str(date) for date in closed_days]
    closed_days_json = json.dumps(closed_days_list)
    
    # Get active time slots from database
    from .models import TimeSlot
    time_slots = TimeSlot.objects.filter(is_active=True).order_by('time')
    time_slots_list = [
        {
            'value': slot.time.strftime('%H:%M'),
            'display': slot.time.strftime('%I:%M %p')
        }
        for slot in time_slots
    ]
    time_slots_json = json.dumps(time_slots_list)
    
    # Get booked appointments grouped by date for calendar display
    from django.db.models import Q
    booked_appointments = Appointment.objects.filter(
        Q(status='scheduled') | Q(status='confirmed')
    ).values('appointment_date', 'appointment_time')
    
    # Group booked appointments by date
    booked_slots = {}
    for appt in booked_appointments:
        date_str = str(appt['appointment_date'])
        time_str = appt['appointment_time'].strftime('%H:%M')
        if date_str not in booked_slots:
            booked_slots[date_str] = []
        booked_slots[date_str].append(time_str)
    
    booked_slots_json = json.dumps(booked_slots)
    
    context = {
        'appointment': appointment,
        'closed_days': closed_days_json,
        'time_slots': time_slots_json,
        'booked_slots': booked_slots_json,
        'keep_attendant': keep_attendant,
        'original_attendant': original_attendant,
        'original_attendant_id': original_attendant.id if original_attendant else None,
    }
    
    return render(request, 'appointments/request_reschedule.html', context)


@login_required
def submit_feedback(request, appointment_id):
    """Submit feedback for a completed appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)
    
    if appointment.status != 'completed':
        messages.error(request, 'Feedback can only be submitted for completed appointments.')
        return redirect('appointments:my_appointments')
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        attendant_rating = request.POST.get('attendant_rating')
        comment = request.POST.get('comment', '')
        
        if not rating:
            messages.error(request, 'Please provide a rating for the appointment.')
            return redirect('appointments:my_appointments')
        
        rating = int(rating)
        if rating < 1 or rating > 5:
            messages.error(request, 'Appointment rating must be between 1 and 5.')
            return redirect('appointments:my_appointments')
        
        # Validate attendant rating if provided
        attendant_rating_int = None
        if attendant_rating:
            attendant_rating_int = int(attendant_rating)
            if attendant_rating_int < 1 or attendant_rating_int > 5:
                messages.error(request, 'Attendant rating must be between 1 and 5.')
                return redirect('appointments:my_appointments')
        
        # Check if feedback already exists
        from .models import Feedback
        if Feedback.objects.filter(appointment=appointment, patient=request.user).exists():
            messages.error(request, 'You have already submitted feedback for this appointment.')
            return redirect('appointments:my_appointments')
        
        # Create feedback
        Feedback.objects.create(
            appointment=appointment,
            patient=request.user,
            rating=rating,
            attendant_rating=attendant_rating_int,
            comment=comment
        )
        
        messages.success(request, 'Thank you for your feedback!')
        return redirect('appointments:my_appointments')
    
    return redirect('appointments:my_appointments')


@csrf_exempt
@require_http_methods(["GET"])
def get_notifications_api(request):
    """API endpoint to get notifications (replaces get_notifications.php)"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Not authenticated'})
    
    try:
        from django.db.models import Q
        
        if request.user.user_type == 'admin':
            # For admin/staff, show all system notifications (where patient is null)
            notifications = Notification.objects.filter(patient__isnull=True, is_read=False).order_by('-created_at')[:10]
        elif request.user.user_type == 'owner':
            # For owner, show all system notifications (where patient is null)
            notifications = Notification.objects.filter(patient__isnull=True, is_read=False).order_by('-created_at')[:10]
        elif request.user.user_type == 'attendant':
            # For attendant, show notifications assigned to them or system notifications
            notifications = Notification.objects.filter(
                (Q(patient=request.user) | Q(patient__isnull=True)),
                is_read=False
            ).order_by('-created_at')[:10]
        else:
            # For patients, show their notifications
            notifications = Notification.objects.filter(patient=request.user, is_read=False).order_by('-created_at')[:10]
        
        # Count unread notifications
        unread_count = notifications.count()
        
        # Format notifications
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'notification_id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'is_read': notification.is_read,
                'created_at_formatted': notification.created_at.strftime('%Y-%m-%d %I:%M %p')
            })
        
        return JsonResponse({
            'success': True,
            'notifications': notifications_data,
            'unread_count': unread_count
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def update_notifications_api(request):
    """API endpoint to update notifications (replaces update_notifications.php)"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Not authenticated'})
    
    try:
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            import json
            data = json.loads(request.body)
            action = data.get('action')
            notification_id = data.get('notification_id')
        else:
            action = request.POST.get('action')
            notification_id = request.POST.get('notification_id')
        
        if action == 'mark_read':
            if notification_id:
                notification = get_object_or_404(Notification, id=notification_id)
                # Allow admin, owner, or the notification's patient to mark as read
                if request.user.user_type in ('admin', 'owner'):
                    # For admin/owner, only allow marking system notifications (patient is None)
                    if notification.patient is None:
                        notification.is_read = True
                        notification.save()
                        return JsonResponse({'success': True})
                elif notification.patient == request.user:
                    notification.is_read = True
                    notification.save()
                    return JsonResponse({'success': True})
        
        elif action == 'mark_all_read':
            if request.user.user_type in ('admin', 'owner'):
                Notification.objects.filter(patient__isnull=True).update(is_read=True)
            else:
                Notification.objects.filter(patient=request.user).update(is_read=True)
            return JsonResponse({'success': True})
        
        return JsonResponse({'success': False, 'error': 'Invalid action'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def manage_attendants(request):
    """Manage attendant accounts"""
    attendants = User.objects.filter(user_type='attendant').order_by('first_name', 'last_name')
    
    if request.method == 'POST':
        form = AttendantForm(request.POST)
        if form.is_valid():
            # Validate schedule selection
            if not form.cleaned_data['schedule']:
                form.add_error('schedule', 'Please select a schedule.')
            else:
                # Save attendant profile
                profile = form.save(commit=False)
                profile.user_type = 'attendant'
                profile.save()
                
                messages.success(request, 'Attendant account updated successfully.')
                return redirect('accounts:manage_attendants')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AttendantForm()
    
    context = {
        'attendants': attendants,
        'form': form,
    }
    
    return render(request, 'accounts/manage_attendants.html', context)


# ===========================
# ATTENDANT UNAVAILABILITY API ENDPOINTS
# ===========================

@login_required
def api_unavailability_details(request, appointment_id):
    """
    API endpoint to get appointment details and unavailability request info
    """
    try:
        appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)
        
        # Get the pending unavailability request for this appointment
        from .models import AttendantUnavailabilityRequest
        unavailability_request = appointment.unavailability_requests.filter(
            status='pending',
            pending_reassignment_choice=True
        ).first()
        
        if not unavailability_request:
            return JsonResponse({
                'success': False,
                'error': 'No pending unavailability request found for this appointment.'
            })
        
        # Format appointment details
        service_name = "Product Purchase"
        if appointment.service:
            service_name = appointment.service.service_name
        elif appointment.package:
            service_name = appointment.package.package_name
        elif appointment.product:
            service_name = f"Product: {appointment.product.product_name}"
        
        attendant_name = appointment.attendant.get_full_name() if appointment.attendant else "Not assigned"
        
        return JsonResponse({
            'success': True,
            'unavailability_request_id': unavailability_request.id,
            'service_name': service_name,
            'appointment_date': appointment.appointment_date.strftime('%B %d, %Y'),
            'appointment_time': appointment.appointment_time.strftime('%I:%M %p'),
            'attendant_name': attendant_name,
            'attendant_id': appointment.attendant.id if appointment.attendant else None,
            'reason': unavailability_request.reason
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def api_available_attendants(request):
    """
    API endpoint to get available attendants for a specific date/time
    Excludes the original attendant from the list
    """
    try:
        date_str = request.GET.get('date')
        time_str = request.GET.get('time')
        exclude_attendant_id = request.GET.get('exclude_attendant_id')
        
        if not date_str or not time_str:
            return JsonResponse({
                'success': False,
                'error': 'Date and time parameters are required'
            })
        
        # Parse date and time
        appointment_date = datetime.strptime(date_str, '%B %d, %Y').date()
        appointment_time = datetime.strptime(time_str, '%I:%M %p').time()
        
        # Format for get_available_attendants function
        date_formatted = appointment_date.strftime('%Y-%m-%d')
        time_formatted = appointment_time.strftime('%H:%M')
        
        # Get available attendants
        available_attendants = get_available_attendants(date_formatted, time_formatted)
        
        # Filter out the original attendant if specified
        if exclude_attendant_id:
            available_attendants = available_attendants.exclude(id=int(exclude_attendant_id))
        
        attendants_data = [
            {
                'id': attendant.id,
                'name': attendant.get_full_name()
            }
            for attendant in available_attendants
        ]
        
        return JsonResponse({
            'success': True,
            'attendants': attendants_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def respond_to_unavailable_attendant(request, unavailability_request_id):
    """
    Handle patient's response to attendant unavailability
    Processes the 3 choices: choose_another, reschedule_same, or cancel
    """
    from .models import AttendantUnavailabilityRequest, HistoryLog
    from services.sms_service import sms_service
    
    try:
        unavailability_request = get_object_or_404(
            AttendantUnavailabilityRequest,
            id=unavailability_request_id
        )
        
        # Verify the appointment belongs to the current user
        if unavailability_request.appointment.patient != request.user:
            return JsonResponse({
                'success': False,
                'error': 'You do not have permission to respond to this request.'
            })
        
        choice = request.POST.get('choice')
        
        if choice == 'choose_another':
            # Option 1: Choose another attendant
            new_attendant_id = request.POST.get('new_attendant_id')
            
            if not new_attendant_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Please select a new attendant.'
                })
            
            new_attendant = get_object_or_404(User, id=new_attendant_id, user_type='attendant')
            appointment = unavailability_request.appointment
            old_attendant = appointment.attendant
            
            # Update appointment with new attendant
            appointment.attendant = new_attendant
            appointment.save()
            
            # Update unavailability request
            unavailability_request.patient_choice = 'choose_another'
            unavailability_request.status = 'resolved'
            unavailability_request.pending_reassignment_choice = False
            unavailability_request.resolved_at = timezone.now()
            unavailability_request.save()
            
            # Mark notification as read
            Notification.objects.filter(
                patient=request.user,
                appointment_id=appointment.id,
                title__icontains='Attendant Unavailable'
            ).update(is_read=True)
            
            # Send success SMS to patient
            try:
                message = f"Hi {request.user.first_name}, your appointment on {appointment.appointment_date.strftime('%B %d, %Y')} at {appointment.appointment_time.strftime('%I:%M %p')} has been updated with a new attendant: {new_attendant.get_full_name()}."
                sms_service.send_sms(request.user.phone, message)
            except Exception as e:
                logger.error(f"Failed to send confirmation SMS: {str(e)}")
            
            # Create notification for staff
            Notification.objects.create(
                type='system',
                title='Patient Choice: New Attendant Selected',
                message=f"Patient {request.user.get_full_name()} chose to keep their appointment on {appointment.appointment_date.strftime('%B %d, %Y')} at {appointment.appointment_time.strftime('%I:%M %p')} and selected {new_attendant.get_full_name()} as their new attendant.",
            )
            
            # Log the action
            HistoryLog.objects.create(
                action_type='edit',
                item_type='appointment',
                item_id=appointment.id,
                performed_by=request.user,
                details={
                    'appointment_id': appointment.id,
                    'action': 'attendant_reassignment',
                    'old_attendant': old_attendant.get_full_name() if old_attendant else 'None',
                    'new_attendant': new_attendant.get_full_name(),
                    'patient_choice': 'choose_another'
                }
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Your appointment has been updated with {new_attendant.get_full_name()}.'
            })
        
        elif choice == 'reschedule_same':
            # Option 2: Reschedule with same attendant
            unavailability_request.patient_choice = 'reschedule_same'
            unavailability_request.pending_reassignment_choice = False
            unavailability_request.save()
            
            return JsonResponse({
                'success': True,
                'redirect': f'/appointments/request-reschedule/{unavailability_request.appointment.id}/?keep_attendant=true'
            })
        
        elif choice == 'cancel':
            # Option 3: Cancel appointment
            unavailability_request.patient_choice = 'cancel'
            unavailability_request.pending_reassignment_choice = False
            unavailability_request.save()
            
            return JsonResponse({
                'success': True,
                'redirect': f'/appointments/request-cancellation/{unavailability_request.appointment.id}/'
            })
        
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid choice. Please select one of the three options.'
            })
            
    except Exception as e:
        logger.error(f"Error in respond_to_unavailable_attendant: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
