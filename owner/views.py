from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q, Max, DecimalField
from django.db.models.functions import TruncMonth, TruncWeek
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from accounts.models import User
from appointments.models import Appointment, ClosedDay
from services.models import Service, ServiceImage, ServiceCategory, HistoryLog
from products.models import Product, ProductImage
from packages.models import Package
from analytics.models import PatientAnalytics, ServiceAnalytics, BusinessAnalytics, TreatmentCorrelation, PatientSegment


def log_history(item_type, item_name, action, performed_by, details='', related_id=None):
    """Helper function to log history and notify owner"""
    from appointments.models import Notification
    from accounts.models import User
    
    # Create history log
    HistoryLog.objects.create(
        type=item_type,
        name=item_name,
        action=action,
        performed_by=performed_by,
        details=details,
        related_id=related_id
    )
    
    # Notify owner when staff performs actions
    owner_users = User.objects.filter(user_type='owner', is_active=True)
    for owner in owner_users:
        Notification.objects.create(
            type='system',
            title=f'{action}: {item_type} - {item_name}',
            message=f'{performed_by} {action.lower()} {item_type.lower()} "{item_name}". {details}',
            patient=None  # Owner notification
        )


def is_owner(user):
    """Check if user is owner or admin (staff)"""
    return user.is_authenticated and user.user_type in ('owner', 'admin')


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_dashboard(request):
    """Owner dashboard - same as staff analytics"""
    from appointments.models import Notification, Appointment
    from django.db.models import Q, Count, Sum, Max
    from datetime import timedelta, datetime
    from django.utils import timezone
    from dateutil.relativedelta import relativedelta
    
    # Get filter parameters from request
    # Define today first since it's used in defaults
    today = timezone.now().date()
    
    time_period = request.GET.get('time_period', 'last_3_months')
    
    # Calculate date range based on time period
    if time_period == 'custom':
        # Custom date range from month/year selectors
        from_month = int(request.GET.get('from_month', 1))
        to_month = int(request.GET.get('to_month', 12))
        from_year = int(request.GET.get('from_year', today.year))
        to_year = int(request.GET.get('to_year', today.year))
        
        filter_start_date = datetime(from_year, from_month, 1).date()
        
        if to_month == 12:
            filter_end_date = datetime(to_year, 12, 31).date()
        else:
            filter_end_date = (datetime(to_year, to_month + 1, 1) - timedelta(days=1)).date()
        
        if filter_end_date > today:
            filter_end_date = today
    else:
        # Preset time periods
        if time_period == 'this_month':
            filter_start_date = today.replace(day=1)
            filter_end_date = today
        elif time_period == 'last_month':
            first_day = today.replace(day=1)
            last_day = first_day - timedelta(days=1)
            filter_start_date = last_day.replace(day=1)
            filter_end_date = last_day
        elif time_period == 'last_3_months':
            filter_start_date = today - timedelta(days=90)
            filter_end_date = today
        elif time_period == 'last_6_months':
            filter_start_date = today - timedelta(days=180)
            filter_end_date = today
        elif time_period == 'last_12_months':
            filter_start_date = today - timedelta(days=365)
            filter_end_date = today
        elif time_period == 'year_to_date':
            filter_start_date = today.replace(month=1, day=1)
            filter_end_date = today
        else:
            # Default to this month
            filter_start_date = today.replace(day=1)
            filter_end_date = today
        
        # Set defaults for custom range form
        from_month = filter_start_date.month
        to_month = filter_end_date.month
        from_year = filter_start_date.year
        to_year = filter_end_date.year
    
    # Base queryset for appointments with select_related for optimization
    appointments_qs = Appointment.objects.select_related(
        'patient', 'attendant', 'service', 'product', 'package'
    ).filter(
        appointment_date__gte=filter_start_date,
        appointment_date__lte=filter_end_date
    )
    
    # Optimize: Get all statistics in fewer queries
    completed_qs = appointments_qs.filter(status='completed')
    
    # Basic statistics (filtered) - optimized single query
    total_appointments_filtered = appointments_qs.count()
    
    # Calculate revenue in one query - optimized
    total_revenue_filtered = completed_qs.aggregate(
        service_revenue=Sum('service__price'),
        product_revenue=Sum('product__price'),
        package_revenue=Sum('package__price')
    )
    total_revenue_filtered = (
        (total_revenue_filtered['service_revenue'] or 0) +
        (total_revenue_filtered['product_revenue'] or 0) +
        (total_revenue_filtered['package_revenue'] or 0)
    )
    
    # Overall statistics (unfiltered) - cache these if possible
    total_patients = User.objects.filter(user_type='patient').count()
    total_appointments = Appointment.objects.count()
    total_revenue = Appointment.objects.filter(
        status='completed'
    ).aggregate(
        total=Sum('service__price'),
        product_total=Sum('product__price'),
        package_total=Sum('package__price')
    )
    total_revenue = (
        (total_revenue['total'] or 0) +
        (total_revenue['product_total'] or 0) +
        (total_revenue['package_total'] or 0)
    )
    
    # Recent activity (filtered) - already optimized with select_related
    recent_appointments = appointments_qs.order_by('-appointment_date')[:20]
    
    # Patient analytics (filtered) - optimized
    active_patients = appointments_qs.values('patient').distinct().count()
    new_patients = User.objects.filter(
        user_type='patient',
        created_at__gte=filter_start_date,
        created_at__lte=filter_end_date
    ).count()
    
    # Get at_risk patients count safely - cache this
    try:
        at_risk_count = PatientSegment.objects.filter(segment='at_risk').count()
    except Exception:
        at_risk_count = 0
    
    patient_stats = {
        'new_patients_30_days': new_patients,
        'active_patients': active_patients,
        'at_risk_patients': at_risk_count,
    }
    
    # Calculate churn patterns - diagnostic analytics showing WHY patients leave
    # Get all patients with their completed appointment counts and last appointment date
    patients_with_visits = User.objects.filter(
        user_type='patient',
        appointments__status='completed'
    ).annotate(
        visit_count=Count('appointments', filter=Q(appointments__status='completed')),
        last_visit=Max('appointments__appointment_date', filter=Q(appointments__status='completed'))
    ).distinct()
    
    # One-time customers (exactly 1 completed visit)
    one_time_customers = patients_with_visits.filter(visit_count=1).count()
    
    # Early dropoff (2-3 completed visits, haven't returned in 90+ days)
    early_dropoff = patients_with_visits.filter(
        visit_count__range=(2, 3),
        last_visit__lt=today - timedelta(days=90)
    ).count()
    
    # Lost regulars (4+ completed visits, haven't returned in 120+ days)
    lost_regulars = patients_with_visits.filter(
        visit_count__gte=4,
        last_visit__lt=today - timedelta(days=120)
    ).count()
    
    # Active regulars (4+ completed visits, returned within 120 days)
    active_regulars = patients_with_visits.filter(
        visit_count__gte=4,
        last_visit__gte=today - timedelta(days=120)
    ).count()
    
    churn_patterns = {
        'one_time_customers': one_time_customers,
        'early_dropoff': early_dropoff,
        'lost_regulars': lost_regulars,
        'active_regulars': active_regulars,
    }
    
    # Service Quality Impact on Retention - diagnostic analytics showing WHY some services retain better
    # Calculate average rating and retention rate per service
    from appointments.models import Feedback
    from django.db.models import F
    
    services_with_bookings = Service.objects.filter(
        appointments__status='completed'
    ).annotate(
        total_bookings=Count('appointments', filter=Q(appointments__status='completed'), distinct=True),
        avg_rating=Avg('appointments__feedback__rating'),
        total_patients=Count('appointments__patient', filter=Q(appointments__status='completed'), distinct=True)
    ).filter(total_bookings__gte=5)  # Minimum 5 bookings for statistical relevance
    
    service_quality_data = []
    for service in services_with_bookings:
        # Calculate retention rate: % of patients who booked this service 2+ times
        repeat_patients = User.objects.filter(
            user_type='patient',
            appointments__service=service,
            appointments__status='completed'
        ).annotate(
            visit_count=Count('appointments', filter=Q(appointments__service=service, appointments__status='completed'))
        ).filter(visit_count__gte=2).count()
        
        retention_rate = (repeat_patients / service.total_patients * 100) if service.total_patients > 0 else 0
        
        # Generate insight based on rating vs retention correlation
        if service.avg_rating and service.avg_rating >= 4.5 and retention_rate >= 60:
            insight = "Excellent - High satisfaction drives loyalty"
        elif service.avg_rating and service.avg_rating >= 4.0 and retention_rate >= 40:
            insight = "Good - Solid performance"
        elif service.avg_rating and service.avg_rating < 3.5 and retention_rate < 30:
            insight = "Critical - Poor quality causing churn"
        elif service.avg_rating and service.avg_rating < 4.0 and retention_rate < 40:
            insight = "Warning - Quality issues affecting retention"
        else:
            insight = "Monitor - Mixed performance"
        
        service_quality_data.append({
            'service_name': service.service_name,
            'avg_rating': round(service.avg_rating, 2) if service.avg_rating else 0,
            'retention_rate': round(retention_rate, 1),
            'total_bookings': service.total_bookings,
            'insight': insight
        })
    
    # Sort by retention rate descending to find best/worst performers
    service_quality_data = sorted(service_quality_data, key=lambda x: x['retention_rate'], reverse=True)
    
    # Service popularity (filtered) - optimized with select_related
    if appointments_qs.exists():
        # Use values to avoid loading full objects
        service_ids = appointments_qs.exclude(service__isnull=True).values_list('service_id', flat=True).distinct()
        popular_services = Service.objects.filter(
            id__in=service_ids
        ).annotate(
            booking_count=Count('appointments', filter=Q(appointments__in=appointments_qs))
        ).order_by('-booking_count')[:10]
    else:
        popular_services = Service.objects.none()
    
    # Status breakdown - optimized
    status_breakdown = appointments_qs.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Treatment correlations - limit and optimize
    try:
        correlations = TreatmentCorrelation.objects.select_related(
            'primary_service', 'secondary_service'
        ).filter(
            correlation_strength__gte=0.5
        ).order_by('-correlation_strength')[:10]
    except Exception:
        correlations = TreatmentCorrelation.objects.none()
    
    # Patient segments - optimized
    try:
        segments = PatientSegment.objects.values('segment').annotate(
            count=Count('id')
        ).order_by('-count')
    except Exception:
        segments = []
    
    # Get notification count (owner notifications are where patient is null)
    notification_count = Notification.objects.filter(
        patient__isnull=True,
        is_read=False
    ).count()
    
    # Get attendants for filter dropdown - ONLY ACTIVE attendants
    try:
        # Filter for active attendants only
        attendants = User.objects.filter(user_type='attendant', is_active=True).order_by('first_name', 'last_name')
    except Exception:
        attendants = []
    
    # === DYNAMIC ANALYTICS CALCULATIONS ===
    
    # Calculate completion rate
    completed_count = sum(s['count'] for s in status_breakdown if s['status'] == 'completed')
    completion_rate = (completed_count / total_appointments_filtered * 100) if total_appointments_filtered > 0 else 0
    
    # Calculate cancellation rate
    cancelled_count = sum(s['count'] for s in status_breakdown if s['status'] == 'cancelled')
    cancellation_rate = (cancelled_count / total_appointments_filtered * 100) if total_appointments_filtered > 0 else 0
    
    # Determine cancellation severity
    if cancellation_rate >= 20:
        cancellation_severity = 'critical'
        cancellation_message = 'Critical: Immediate intervention required'
    elif cancellation_rate >= 10:
        cancellation_severity = 'warning'
        cancellation_message = 'Moderate concern - review policies'
    else:
        cancellation_severity = 'good'
        cancellation_message = 'Healthy cancellation rate'
    
    # Calculate patient retention metrics
    retention_rate = (active_patients / total_patients * 100) if total_patients > 0 else 0
    at_risk_percentage = (at_risk_count / total_patients * 100) if total_patients > 0 else 0
    
    # Determine retention health
    if retention_rate >= 70:
        retention_health = 'excellent'
        retention_message = 'Strong patient retention'
    elif retention_rate >= 50:
        retention_health = 'good'
        retention_message = 'Moderate retention - improvement needed'
    else:
        retention_health = 'poor'
        retention_message = 'Critical: High patient churn'
    
    # Service diversity analysis
    service_count = popular_services.count()
    if service_count > 0:
        top_service_bookings = popular_services.first().booking_count if popular_services.exists() else 0
        total_service_bookings = sum(s.booking_count for s in popular_services)
        service_concentration = (top_service_bookings / total_service_bookings * 100) if total_service_bookings > 0 else 0
        
        if service_concentration >= 40:
            service_diversity = 'low'
            service_diversity_message = 'Over-reliance on top service'
        elif service_concentration >= 25:
            service_diversity = 'moderate'
            service_diversity_message = 'Balanced service distribution'
        else:
            service_diversity = 'high'
            service_diversity_message = 'Well-diversified service portfolio'
    else:
        service_concentration = 0
        service_diversity = 'none'
        service_diversity_message = 'No service data available'
    
    # Churn pattern analysis - diagnostic analytics
    total_churn = one_time_customers + early_dropoff + lost_regulars
    
    # Determine primary churn segment
    churn_segments = {
        'one_time_customers': one_time_customers,
        'early_dropoff': early_dropoff,
        'lost_regulars': lost_regulars,
        'active_regulars': active_regulars
    }
    
    # Find the highest churn segment (excluding active regulars)
    churn_only = {k: v for k, v in churn_segments.items() if k != 'active_regulars'}
    churn_primary_segment = max(churn_only, key=churn_only.get) if any(churn_only.values()) else 'active_regulars'
    churn_primary_count = churn_segments[churn_primary_segment]
    
    # Generate dynamic insights based on primary churn segment
    if churn_primary_segment == 'one_time_customers' and one_time_customers > 0:
        churn_message = f'CRITICAL: {one_time_customers} customers left after first visit - poor first impression'
        churn_action = 'Audit first-visit experience: check service quality, attendant performance, and follow-up procedures'
    elif churn_primary_segment == 'early_dropoff' and early_dropoff > 0:
        churn_message = f'WARNING: {early_dropoff} customers dropped off after 2-3 visits - pricing or quality issue'
        churn_action = 'Review pricing strategy, service quality consistency, and gather feedback from 2-3 visit customers'
    elif churn_primary_segment == 'lost_regulars' and lost_regulars > 0:
        churn_message = f'ATTENTION: {lost_regulars} regular customers (4+ visits) stopped returning - competition or life changes'
        churn_action = 'Launch re-engagement campaign: personalized offers, "We miss you" messages, and loyalty incentives'
    else:
        churn_message = f'EXCELLENT: {active_regulars} active regular customers maintain strong loyalty'
        churn_action = 'Continue current retention strategies and reward loyal customers with exclusive benefits'
    
    # Revenue trend analysis
    avg_revenue_per_appointment = (total_revenue_filtered / total_appointments_filtered) if total_appointments_filtered > 0 else 0
    
    if avg_revenue_per_appointment >= 1500:
        revenue_trend = 'high'
        revenue_message = 'Excellent revenue per appointment'
    elif avg_revenue_per_appointment >= 800:
        revenue_trend = 'moderate'
        revenue_message = 'Moderate revenue - upselling opportunity'
    else:
        revenue_trend = 'low'
        revenue_message = 'Low revenue - review pricing strategy'
    
    # Peak performance analysis
    if completion_rate >= 80:
        performance_status = 'excellent'
        performance_message = 'Outstanding appointment completion rate'
    elif completion_rate >= 60:
        performance_status = 'good'
        performance_message = 'Good performance with room for improvement'
    else:
        performance_status = 'poor'
        performance_message = 'Low completion rate - investigate issues'
    
    # Service Quality Impact Analysis - diagnostic insights
    if service_quality_data:
        worst_service = service_quality_data[-1]  # Last item has lowest retention
        best_service = service_quality_data[0]  # First item has highest retention
        
        # Identify critical quality issues
        critical_services = [s for s in service_quality_data if s['avg_rating'] < 3.5 and s['retention_rate'] < 30]
        
        if critical_services:
            service_quality_severity = 'critical'
            service_quality_message = f"URGENT: {len(critical_services)} service(s) with poor ratings (<3.5) causing customer loss"
            service_quality_action = f"Immediate audit of '{worst_service['service_name']}' - {worst_service['retention_rate']}% retention, {worst_service['avg_rating']}/5 rating"
        elif worst_service['retention_rate'] < 40:
            service_quality_severity = 'warning'
            service_quality_message = f"WARNING: '{worst_service['service_name']}' has low retention ({worst_service['retention_rate']}%)"
            service_quality_action = f"Review quality and pricing of '{worst_service['service_name']}' - customers not returning"
        else:
            service_quality_severity = 'good'
            service_quality_message = f"STRONG: '{best_service['service_name']}' achieves {best_service['retention_rate']}% retention with {best_service['avg_rating']}/5 rating"
            service_quality_action = f"Maintain quality standards - replicate '{best_service['service_name']}' success across other services"
    else:
        service_quality_severity = 'info'
        service_quality_message = 'Insufficient feedback data for service quality analysis'
        service_quality_action = 'Encourage patients to provide feedback after appointments to enable quality tracking'
    
    # Analytics insights object
    analytics_insights = {
        'completion_rate': round(completion_rate, 1),
        'cancellation_rate': round(cancellation_rate, 1),
        'cancellation_severity': cancellation_severity,
        'cancellation_message': cancellation_message,
        'cancelled_count': cancelled_count,
        'churn_primary_segment': churn_primary_segment,
        'churn_message': churn_message,
        'churn_action': churn_action,
        'service_quality_severity': service_quality_severity,
        'service_quality_message': service_quality_message,
        'service_quality_action': service_quality_action,
        'retention_rate': round(retention_rate, 1),
        'retention_health': retention_health,
        'retention_message': retention_message,
        'at_risk_percentage': round(at_risk_percentage, 1),
        'service_concentration': round(service_concentration, 1),
        'service_diversity': service_diversity,
        'service_diversity_message': service_diversity_message,
        'avg_revenue_per_appointment': round(avg_revenue_per_appointment, 2),
        'revenue_trend': revenue_trend,
        'revenue_message': revenue_message,
        'performance_status': performance_status,
        'performance_message': performance_message,
    }
    
    context = {
        'total_patients': total_patients,
        'total_appointments': total_appointments,
        'total_revenue': total_revenue,
        'total_appointments_filtered': total_appointments_filtered,
        'total_revenue_filtered': total_revenue_filtered,
        'patient_stats': patient_stats,
        'churn_patterns': churn_patterns,
        'service_quality_data': service_quality_data,
        'popular_services': popular_services,
        'correlations': correlations,
        'segments': segments,
        'recent_appointments': recent_appointments,
        'status_breakdown': status_breakdown,
        'attendants': attendants,
        'notification_count': notification_count,
        'analytics_insights': analytics_insights,
        # Filter values for template
        'time_period': time_period,
        'from_month': from_month,
        'to_month': to_month,
        'from_year': from_year,
        'to_year': to_year,
        'filter_start_date': filter_start_date,
        'filter_end_date': filter_end_date,
    }
    
    return render(request, 'owner/dashboard.html', context)


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_patients(request):
    """Owner patients overview"""
    from decimal import Decimal
    from django.db.models import Case, When, Value, F, OuterRef, Subquery
    from django.db.models.functions import Coalesce
    
    # Get all patients with database-side analytics to avoid N+1 queries
    patients = (
        User.objects.filter(user_type='patient')
        .prefetch_related('segments')
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
            # Get service price sum for completed appointments
            service_spent=Coalesce(
                Sum(
                    'appointments__service__price',
                    filter=Q(appointments__status='completed', appointments__service__isnull=False),
                    output_field=DecimalField(),
                ),
                Value(Decimal('0.00')),
            ),
            # Get package price sum
            package_spent=Coalesce(
                Sum(
                    'appointments__package__price',
                    filter=Q(appointments__status='completed', appointments__package__isnull=False),
                    output_field=DecimalField(),
                ),
                Value(Decimal('0.00')),
            ),
            # Get product price sum (price * quantity)
            product_spent=Coalesce(
                Sum(
                    F('appointments__product__price') * F('appointments__quantity'),
                    filter=Q(appointments__status='completed', appointments__product__isnull=False),
                    output_field=DecimalField(),
                ),
                Value(Decimal('0.00')),
            ),
            last_visit=Max(
                'appointments__appointment_date',
                filter=Q(appointments__status='completed'),
            ),
        )
        .order_by('-id')
    )
    
    # Add pagination BEFORE converting to list
    paginator = Paginator(patients, 20)  # 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Build analytics list with computed total_spent
    patient_analytics_list = [
        {
            'patient': patient,
            'total_appointments': patient.total_appointments,
            'completed_appointments': patient.completed_appointments,
            'cancelled_appointments': patient.cancelled_appointments,
            'total_spent': patient.service_spent + patient.package_spent + patient.product_spent,
            'last_visit': patient.last_visit,
            'segment': patient.segments.first().segment if patient.segments.exists() else 'unclassified',
        }
        for patient in page_obj
    ]
    
    # Get notification count
    from appointments.models import Notification
    notification_count = Notification.objects.filter(
        patient=request.user,
        is_read=False
    ).count()
    
    context = {
        'patient_analytics': patient_analytics_list,
        'page_obj': page_obj,
        'notification_count': notification_count,
    }
    
    return render(request, 'owner/patients.html', context)


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_view_patient(request, patient_id):
    """View patient details"""
    from decimal import Decimal
    
    patient = get_object_or_404(User, id=patient_id, user_type='patient')
    appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_date')
    
    # Calculate patient statistics
    total_appointments = appointments.count()
    completed_appointments = appointments.filter(status='completed').count()
    cancelled_appointments = appointments.filter(status='cancelled').count()
    
    # Calculate total spent (only completed appointments)
    total_spent = Decimal('0.00')
    for appointment in appointments.filter(status='completed'):
        if appointment.service:
            total_spent += appointment.service.price
        elif appointment.package:
            total_spent += appointment.package.price
        elif appointment.product:
            quantity = appointment.quantity if hasattr(appointment, 'quantity') and appointment.quantity else 1
            total_spent += appointment.product.price * quantity
    
    last_visit = appointments.filter(status='completed').order_by('-appointment_date').first()
    
    context = {
        'patient': patient,
        'appointments': appointments,
        'total_appointments': total_appointments,
        'completed_appointments': completed_appointments,
        'cancelled_appointments': cancelled_appointments,
        'total_spent': total_spent,
        'last_visit': last_visit,
    }
    
    return render(request, 'owner/patient_detail.html', context)


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_appointments(request):
    """Owner appointments overview"""
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    search_query = request.GET.get('search', '')
    
    # Start with all appointments - latest bookings first (by creation time, then appointment date/time)
    appointments = Appointment.objects.all().order_by('-created_at', '-appointment_date', '-appointment_time')
    
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
    }
    
    return render(request, 'owner/appointments.html', context)


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_view_appointment(request, appointment_id):
    """View appointment details"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    context = {
        'appointment': appointment,
    }
    
    return render(request, 'owner/appointment_detail.html', context)


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_cancel_appointment(request, appointment_id):
    """Owner cancel an appointment"""
    from appointments.models import Notification, CancellationRequest
    from services.utils import send_appointment_sms
    
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, 'Cancellation reason is required.')
            return redirect('owner:appointments')
    
    if appointment.status in ['scheduled', 'confirmed']:
        # Get reason from POST or set default
        reason = request.POST.get('reason', '').strip() if request.method == 'POST' else 'Cancelled by owner'
        
        appointment.status = 'cancelled'
        appointment.save()
        
        # Create cancellation request record with reason
        appointment_type = 'package' if appointment.package else 'regular'
        CancellationRequest.objects.create(
            appointment_id=appointment.id,
            appointment_type=appointment_type,
            patient=appointment.patient,
            reason=reason,
            status='approved'  # Auto-approved since owner is cancelling
        )
        
        # Create notification for patient
        Notification.objects.create(
            type='cancellation',
            appointment_id=appointment.id,
            title='Appointment Cancelled',
            message=f'Your appointment for {appointment.get_service_name()} on {appointment.appointment_date} at {appointment.appointment_time} has been cancelled. Please contact us to reschedule.',
            patient=appointment.patient
        )
        
        # Notify owner of appointment cancellation (self-notification)
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
    else:
        messages.error(request, 'Only pending or confirmed appointments can be cancelled.')
    
    return redirect('owner:appointments')


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_reschedule_appointment(request, appointment_id):
    """Owner reschedule an appointment"""
    from appointments.models import Notification, RescheduleRequest
    from services.utils import send_appointment_sms
    
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method == 'POST':
        new_date = request.POST.get('new_appointment_date')
        new_time = request.POST.get('new_appointment_time')
        reason = request.POST.get('reason', '').strip()
        
        if not new_date or not new_time:
            messages.error(request, 'Please provide both new date and time.')
            return redirect('owner:appointments')
        
        # Check if appointment can be rescheduled
        if appointment.status not in ['pending', 'confirmed']:
            messages.error(request, 'This appointment cannot be rescheduled.')
            return redirect('owner:appointments')
        
        # Check if the new date is a closed clinic day
        new_date_obj = datetime.strptime(new_date, "%Y-%m-%d").date()
        if ClosedDay.objects.filter(date=new_date_obj).exists():
            closed_day = ClosedDay.objects.get(date=new_date_obj)
            reason_text = f" ({closed_day.reason})" if closed_day.reason else ""
            messages.error(request, f'Cannot reschedule: The clinic is closed on {new_date_obj.strftime("%B %d, %Y")}{reason_text}.')
            return redirect('owner:appointments')
        
        # Create reschedule request (mark as approved since owner is rescheduling)
        reschedule_request = RescheduleRequest.objects.create(
            appointment_id=appointment.id,
            new_appointment_date=new_date,
            new_appointment_time=new_time,
            patient=appointment.patient,
            reason=reason or 'Rescheduled by owner',
            status='approved'  # Auto-approve owner reschedules
        )
        
        # Update appointment
        old_date = appointment.appointment_date
        old_time = appointment.appointment_time
        appointment.appointment_date = new_date
        appointment.appointment_time = new_time
        appointment.status = 'pending'  # Set to pending after reschedule
        appointment.save()
        
        # Create notification for patient
        Notification.objects.create(
            type='reschedule',
            appointment_id=appointment.id,
            title='Appointment Rescheduled',
            message=f'Your appointment for {appointment.get_service_name()} has been rescheduled from {old_date} at {old_time} to {new_date} at {new_time}. Reason: {reason or "Rescheduled by clinic"}.',
            patient=appointment.patient
        )
        
        # Notify owner (self-notification)
        Notification.objects.create(
            type='reschedule',
            appointment_id=appointment.id,
            title='Appointment Rescheduled',
            message=f'Appointment for {appointment.patient.get_full_name()} - {appointment.get_service_name()} has been rescheduled from {old_date} at {old_time} to {new_date} at {new_time}.',
            patient=None  # Owner notification
        )
        
        # Send SMS notification
        sms_result = send_appointment_sms(appointment, 'reschedule')
        if sms_result['success']:
            messages.success(request, f'Appointment for {appointment.patient.full_name} has been rescheduled. SMS sent.')
        else:
            messages.success(request, f'Appointment for {appointment.patient.full_name} has been rescheduled. (SMS failed)')
        
        return redirect('owner:appointments')
    
    # GET request - show reschedule form
    context = {
        'appointment': appointment,
    }
    
    return render(request, 'owner/reschedule_appointment.html', context)


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_services(request):
    """Owner services overview"""
    services = Service.objects.filter(archived=False).annotate(
        total_bookings=Count('appointments'),
        completed_bookings=Count('appointments', filter=Q(appointments__status='completed')),
        cancelled_bookings=Count('appointments', filter=Q(appointments__status='cancelled')),
        total_revenue=Sum('appointments__service__price', filter=Q(appointments__status='completed')),
        avg_rating=Avg('appointments__feedback__rating', filter=Q(appointments__feedback__isnull=False))
    ).order_by('-total_revenue')
    
    # Add pagination
    paginator = Paginator(services, 15)  # 15 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'services': page_obj,
        'page_obj': page_obj,
    }
    
    return render(request, 'owner/services.html', context)


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_packages(request):
    """Owner packages overview"""
    packages = Package.objects.filter(archived=False).annotate(
        total_bookings=Count('package_bookings'),
        total_revenue=Sum('package_bookings__price'),
        avg_rating=Avg('package_bookings__feedback__rating', filter=Q(package_bookings__feedback__isnull=False))
    ).order_by('-total_revenue')
    
    # Add pagination
    paginator = Paginator(packages, 15)  # 15 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'packages': page_obj,
        'page_obj': page_obj,
    }
    
    return render(request, 'owner/packages.html', context)


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_products(request):
    """Owner products overview"""
    products = Product.objects.annotate(
        total_bookings=Count('appointments'),
        completed_bookings=Count('appointments', filter=Q(appointments__status='completed')),
        total_revenue=Sum('appointments__product__price', filter=Q(appointments__status='completed'))
    ).order_by('-total_revenue')
    
    # Add pagination
    paginator = Paginator(products, 15)  # 15 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'page_obj': page_obj,
    }
    
    return render(request, 'owner/products.html', context)


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_analytics(request):
    """Owner analytics dashboard - same as staff analytics"""
    # Get filter parameters from request
    date_range = request.GET.get('date_range', '30')
    status_filter = request.GET.get('status', '')
    service_type_filter = request.GET.get('service_type', '')
    attendant_filter = request.GET.get('attendant', '')
    patient_search = request.GET.get('patient_search', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # Calculate date range
    today = timezone.now().date()
    if date_range == '7':
        filter_start_date = today - timedelta(days=7)
    elif date_range == '90':
        filter_start_date = today - timedelta(days=90)
    elif date_range == '365':
        filter_start_date = today - timedelta(days=365)
    else:
        filter_start_date = today - timedelta(days=30)
    
    # Use custom date range if provided
    if start_date:
        try:
            filter_start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if end_date:
        try:
            filter_end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            filter_end_date = today
    else:
        filter_end_date = today
    
    # Base queryset for appointments with select_related for optimization
    appointments_qs = Appointment.objects.select_related(
        'patient', 'attendant', 'service', 'product', 'package'
    ).filter(
        appointment_date__gte=filter_start_date,
        appointment_date__lte=filter_end_date
    )
    
    # Apply filters
    if status_filter:
        appointments_qs = appointments_qs.filter(status=status_filter)
    
    if service_type_filter == 'service':
        appointments_qs = appointments_qs.exclude(service__isnull=True)
    elif service_type_filter == 'product':
        appointments_qs = appointments_qs.exclude(product__isnull=True)
    elif service_type_filter == 'package':
        appointments_qs = appointments_qs.exclude(package__isnull=True)
    
    if attendant_filter:
        appointments_qs = appointments_qs.filter(attendant_id=attendant_filter)
    
    if patient_search:
        appointments_qs = appointments_qs.filter(
            Q(patient__first_name__icontains=patient_search) |
            Q(patient__last_name__icontains=patient_search) |
            Q(patient__email__icontains=patient_search)
        )
    
    # Optimize: Get all statistics in fewer queries
    completed_qs = appointments_qs.filter(status='completed')
    
    # Basic statistics (filtered) - optimized single query
    total_appointments_filtered = appointments_qs.count()
    
    # Calculate revenue in one query - optimized
    total_revenue_filtered = completed_qs.aggregate(
        service_revenue=Sum('service__price'),
        product_revenue=Sum('product__price'),
        package_revenue=Sum('package__price')
    )
    total_revenue_filtered = (
        (total_revenue_filtered['service_revenue'] or 0) +
        (total_revenue_filtered['product_revenue'] or 0) +
        (total_revenue_filtered['package_revenue'] or 0)
    )
    
    # Overall statistics (unfiltered) - cache these if possible
    total_patients = User.objects.filter(user_type='patient').count()
    total_appointments = Appointment.objects.count()
    total_revenue = Appointment.objects.filter(
        status='completed'
    ).aggregate(
        total=Sum('service__price'),
        product_total=Sum('product__price'),
        package_total=Sum('package__price')
    )
    total_revenue = (
        (total_revenue['total'] or 0) +
        (total_revenue['product_total'] or 0) +
        (total_revenue['package_total'] or 0)
    )
    
    # Recent activity (filtered) - already optimized with select_related
    recent_appointments = appointments_qs.order_by('-appointment_date')[:20]
    
    # Patient analytics (filtered) - optimized
    active_patients = appointments_qs.values('patient').distinct().count()
    new_patients = User.objects.filter(
        user_type='patient',
        created_at__gte=filter_start_date,
        created_at__lte=filter_end_date
    ).count()
    
    # Get at_risk patients count safely - cache this
    try:
        at_risk_count = PatientSegment.objects.filter(segment='at_risk').count()
    except Exception:
        at_risk_count = 0
    
    patient_stats = {
        'new_patients_30_days': new_patients,
        'active_patients': active_patients,
        'at_risk_patients': at_risk_count,
    }
    
    # Service popularity (filtered) - optimized with select_related
    if appointments_qs.exists():
        # Use values to avoid loading full objects
        service_ids = appointments_qs.exclude(service__isnull=True).values_list('service_id', flat=True).distinct()
        popular_services = Service.objects.filter(
            id__in=service_ids
        ).annotate(
            booking_count=Count('appointments', filter=Q(appointments__in=appointments_qs))
        ).order_by('-booking_count')[:10]
    else:
        popular_services = Service.objects.none()
    
    # Status breakdown - optimized
    status_breakdown = appointments_qs.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Treatment correlations - limit and optimize
    try:
        correlations = TreatmentCorrelation.objects.select_related(
            'primary_service', 'secondary_service'
        ).filter(
            correlation_strength__gte=0.5
        ).order_by('-correlation_strength')[:10]
    except Exception:
        correlations = TreatmentCorrelation.objects.none()
    
    # Patient segments - optimized
    try:
        segments = PatientSegment.objects.values('segment').annotate(
            count=Count('id')
        ).order_by('-count')
    except Exception:
        segments = []
    
    # Get attendants for filter dropdown - ONLY ACTIVE attendants
    try:
        # Filter for active attendants only
        attendants = User.objects.filter(user_type='attendant', is_active=True).order_by('first_name', 'last_name')
    except Exception:
        attendants = []
    
    context = {
        'total_patients': total_patients,
        'total_appointments': total_appointments,
        'total_revenue': total_revenue,
        'total_appointments_filtered': total_appointments_filtered,
        'total_revenue_filtered': total_revenue_filtered,
        'patient_stats': patient_stats,
        'popular_services': popular_services,
        'correlations': correlations,
        'segments': segments,
        'recent_appointments': recent_appointments,
        'status_breakdown': status_breakdown,
        'attendants': attendants,
        # Filter values for template
        'date_range': date_range,
        'status_filter': status_filter,
        'service_type_filter': service_type_filter,
        'attendant_filter': attendant_filter,
        'patient_search': patient_search,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'owner/analytics.html', context)


# Owner Management Functions

@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_maintenance(request):
    """Owner maintenance page"""
    
    # Count only active/non-archived items
    services_count = Service.objects.filter(archived=False).count()
    packages_count = Package.objects.filter(archived=False).count()
    products_count = Product.objects.filter(archived=False).count()
    
    # Get filter parameters for history log
    patient_filter = request.GET.get('patient', '')
    treatment_filter = request.GET.get('treatment', '')
    attendant_filter = request.GET.get('attendant', '')
    year_filter = request.GET.get('year', '')
    type_filter = request.GET.get('type', '')
    
    # Get history logs with filtering
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
    
    # Get unique patients for filter
    patients = User.objects.filter(user_type='patient').order_by('first_name', 'last_name')
    
    # Get unique attendants for filter
    attendants = User.objects.filter(user_type='attendant').order_by('first_name', 'last_name')
    
    context = {
        'services_count': services_count,
        'packages_count': packages_count,
        'products_count': products_count,
        'history_logs': history_logs,
        'patient_filter': patient_filter,
        'treatment_filter': treatment_filter,
        'attendant_filter': attendant_filter,
        'year_filter': year_filter,
        'type_filter': type_filter,
        'years': years,
        'patients': patients,
        'attendants': attendants,
    }
    
    return render(request, 'owner/maintenance.html', context)

@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_manage_services(request):
    """Owner manage services"""
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
                    log_history('Service', service_name, 'Added', request.user.get_full_name() or request.user.username, 
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
            log_history('Service', service.service_name, 'Edited', request.user.get_full_name() or request.user.username,
                       f'Updated: {old_name} -> {service.service_name}', service.id)
            messages.success(request, 'Service updated successfully!')
        
        elif action == 'delete' or action == 'archive':
            service_id = request.POST.get('service_id')
            service = get_object_or_404(Service, id=service_id)
            service_name = service.service_name
            service.archived = True
            service.save()
            log_history('Service', service_name, 'Deleted', request.user.get_full_name() or request.user.username,
                       f'Service archived', service.id)
            messages.success(request, 'Service archived successfully!')
        
        return redirect('owner:manage_services')
    
    # Add pagination
    paginator = Paginator(services, 15)  # 15 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = ServiceCategory.objects.all()
    context = {
        'services': page_obj,
        'page_obj': page_obj,
        'categories': categories,
    }
    return render(request, 'owner/manage_services.html', context)


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_manage_packages(request):
    """Owner manage packages"""
    packages = Package.objects.filter(archived=False).order_by('package_name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            package_name = request.POST.get('package_name')
            description = request.POST.get('description')
            price = request.POST.get('price')
            sessions = request.POST.get('sessions')
            duration_days = request.POST.get('duration_days')
            grace_period_days = request.POST.get('grace_period_days')
            
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
                    log_history('Package', package_name, 'Added', request.user.get_full_name() or request.user.username,
                               f'Price: {price}, Sessions: {sessions}', package.id)
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
            log_history('Package', package.package_name, 'Edited', request.user.get_full_name() or request.user.username,
                       f'Updated: {old_name} -> {package.package_name}', package.id)
            messages.success(request, 'Package updated successfully!')
        
        elif action == 'delete' or action == 'archive':
            package_id = request.POST.get('package_id')
            package = get_object_or_404(Package, id=package_id)
            package_name = package.package_name
            package.archived = True
            package.save()
            log_history('Package', package_name, 'Deleted', request.user.get_full_name() or request.user.username,
                       f'Package archived', package.id)
            messages.success(request, 'Package archived successfully!')
        
        return redirect('owner:manage_packages')
    
    # Add pagination
    paginator = Paginator(packages, 15)  # 15 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'packages': page_obj,
        'page_obj': page_obj,
    }
    return render(request, 'owner/manage_packages.html', context)


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_manage_products(request):
    """Owner manage products"""
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
                    messages.success(request, 'Product added successfully!')
                except Exception as e:
                    messages.error(request, f'Error adding product: {str(e)}')
            else:
                messages.error(request, 'Please fill in all required fields.')
        
        elif action == 'edit':
            product_id = request.POST.get('product_id')
            product = get_object_or_404(Product, id=product_id)
            old_name = product.product_name
            product.product_name = request.POST.get('product_name', product.product_name)
            product.description = request.POST.get('description', product.description)
            price = request.POST.get('price')
            if price:
                product.price = price
            stock = request.POST.get('stock') or request.POST.get('stock_quantity')
            if stock is not None:
                product.stock = stock
            product.save()
            log_history('Product', product.product_name, 'Edited', request.user.get_full_name() or request.user.username,
                       f'Updated: {old_name} -> {product.product_name}', product.id)
            messages.success(request, 'Product updated successfully!')
        
        elif action == 'delete' or action == 'archive':
            product_id = request.POST.get('product_id')
            product = get_object_or_404(Product, id=product_id)
            product_name = product.product_name
            product.archived = True
            product.save()
            log_history('Product', product_name, 'Deleted', request.user.get_full_name() or request.user.username,
                       f'Product archived', product.id)
            messages.success(request, 'Product archived successfully!')
        
        return redirect('owner:manage_products')
    
    # Add pagination
    paginator = Paginator(products, 15)  # 15 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'page_obj': page_obj,
    }
    return render(request, 'owner/manage_products.html', context)


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_view_inventory(request):
    """Owner view inventory levels (view-only, no stock management)"""
    products = Product.objects.filter(archived=False).order_by('product_name')
    
    # Add pagination
    paginator = Paginator(products, 15)  # 15 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'page_obj': page_obj,
    }
    return render(request, 'owner/inventory.html', context)


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_manage_patient_profiles(request):
    """Owner view patient profiles - View only (Data Privacy Act compliance)"""
    patients = User.objects.filter(user_type='patient').order_by('-created_at')
    
    if request.method == 'POST':
        # Access control: Owner cannot edit or delete patient profiles
        # Access control matrix specifies: Owner can only VIEW patient profiles
        messages.warning(request, 'Access denied: Owner can only view patient profiles. Editing and deletion are restricted for data privacy compliance.')
        return redirect('owner:manage_patient_profiles')
    
    # Add pagination
    paginator = Paginator(patients, 20)  # 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'patients': page_obj,
        'page_obj': page_obj,
    }
    return render(request, 'owner/manage_patient_profiles.html', context)


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_view_history_log(request):
    """Owner view history log with filtering"""
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
    return render(request, 'owner/history_log.html', context)


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_manage_service_images(request):
    """Owner view to manage service images"""
    services = Service.objects.all().order_by('service_name')
    
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
    paginator = Paginator(services, 15)  # 15 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'services': page_obj,
        'page_obj': page_obj,
    }
    return render(request, 'owner/manage_service_images.html', context)


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_manage_product_images(request):
    """Owner view to manage product images"""
    products = Product.objects.all().order_by('product_name')
    
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
    return render(request, 'owner/manage_product_images.html', context)


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_delete_service_image(request, image_id):
    """Delete a service image"""
    image = get_object_or_404(ServiceImage, id=image_id)
    service_name = image.service.service_name
    image.delete()
    messages.success(request, f'Image deleted successfully for {service_name}')
    return redirect('owner:manage_service_images')


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_delete_product_image(request, image_id):
    """Delete a product image"""
    image = get_object_or_404(ProductImage, id=image_id)
    product_name = image.product.product_name
    image.delete()
    messages.success(request, f'Image deleted successfully for {product_name}')
    return redirect('owner:manage_product_images')


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_set_primary_service_image(request, image_id):
    """Set a service image as primary"""
    image = get_object_or_404(ServiceImage, id=image_id)
    # Unset other primary images for this service
    ServiceImage.objects.filter(service=image.service, is_primary=True).update(is_primary=False)
    # Set this image as primary
    image.is_primary = True
    image.save()
    messages.success(request, f'Primary image updated for {image.service.service_name}')
    return redirect('owner:manage_service_images')


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_set_primary_product_image(request, image_id):
    """Set a product image as primary"""
    image = get_object_or_404(ProductImage, id=image_id)
    # Unset other primary images for this product
    ProductImage.objects.filter(product=image.product, is_primary=True).update(is_primary=False)
    # Set this image as primary
    image.is_primary = True
    image.save()
    messages.success(request, f'Primary image updated for {image.product.product_name}')
    return redirect('owner:manage_product_images')


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


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_manage_attendants(request):
    """Owner manage attendants page - same functionality as admin_settings"""
    from appointments.models import ClosedDay, TimeSlot
    from accounts.models import AttendantProfile
    from django.utils import timezone
    
    attendants = User.objects.filter(user_type='attendant').order_by('first_name', 'last_name')
    closed_days = ClosedDay.objects.all()
    # Get all attendant users for the table (both active and inactive)
    attendant_users = User.objects.filter(user_type='attendant').order_by('username')
    # Get only active attendant users for the calendar view
    active_attendant_users = User.objects.filter(user_type='attendant', is_active=True).order_by('username')
    
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
    
    context = {
        'attendants': attendants,
        'closed_days': closed_days,
        'hours': hours,
        'attendant_users': attendant_users,
        'active_attendant_users': active_attendant_users,
        'attendant_users_with_profiles': attendant_users_with_profiles,
        'attendant_display_names': attendant_display_names,
        'is_today_closed': is_today_closed,
        'today': today,
        'timeslots': timeslots,
        'is_owner': True,  # Flag to indicate this is owner view
    }
    
    return render(request, 'owner/manage_attendants.html', context)


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_create_attendant_user(request):
    """Create a new attendant user account (owner version)"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        
        if not all([username, password, first_name, last_name]):
            messages.error(request, 'Username, password, first name, and last name are required.')
            return redirect('owner:manage_attendants')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'That username is already taken. Please choose another one.')
            return redirect('owner:manage_attendants')
        
        user = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            user_type='attendant',
            is_active=True
        )
        user.set_password(password)
        user.save()
        
        messages.success(request, f'Attendant account {username} created successfully. Temporary password: {password}')
    
    return redirect('owner:manage_attendants')


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_edit_attendant_user(request, user_id):
    """Edit attendant user account (owner version)"""
    user = get_object_or_404(User, id=user_id, user_type='attendant')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        
        if not all([first_name, last_name, username]):
            messages.error(request, 'First name, last name, and username are required.')
            return redirect('owner:manage_attendants')
        
        # Check if username is taken by another user
        if User.objects.filter(username=username).exclude(id=user_id).exists():
            messages.error(request, 'That username is already taken. Please choose another one.')
            return redirect('owner:manage_attendants')
        
        # Update user
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.email = email if email else user.email
        user.middle_name = middle_name if middle_name else user.middle_name
        user.save()
        
        messages.success(request, f'Attendant account {username} has been updated successfully.')
        return redirect('owner:manage_attendants')
    
    return render(request, 'owner/edit_attendant_user.html', {'attendant_user': user, 'is_owner': True})


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_toggle_attendant_user(request, user_id):
    """Activate or deactivate an attendant user account (owner version)"""
    user = get_object_or_404(User, id=user_id, user_type='attendant')
    user.is_active = not user.is_active
    user.archived = not user.is_active
    user.save()
    
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'Attendant account {user.username} has been {status}.')
    return redirect('owner:manage_attendants')


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_reset_attendant_password(request, user_id):
    """Reset attendant account password and provide a temporary one (owner version)"""
    user = get_object_or_404(User, id=user_id, user_type='attendant')
    import secrets
    import string
    chars = string.ascii_letters + string.digits
    temp_password = ''.join(secrets.choice(chars) for _ in range(10))
    user.set_password(temp_password)
    user.save()
    
    messages.success(
        request,
        f'Password for {user.username} has been reset. Temporary password: {temp_password}'
    )
    return redirect('owner:manage_attendants')


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_manage_attendant_profile(request, user_id):
    """Manage attendant profile (work days, hours, phone, and profile picture) (owner version)"""
    from accounts.models import AttendantProfile
    
    user = get_object_or_404(User, id=user_id, user_type='attendant')
    
    if request.method == 'POST':
        work_days = request.POST.getlist('work_days')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        phone = request.POST.get('phone', '').strip()
        
        if not work_days:
            messages.error(request, 'Please select at least one work day.')
            return redirect('owner:manage_attendants')
        
        if not start_time or not end_time:
            messages.error(request, 'Please provide both start and end times.')
            return redirect('owner:manage_attendants')
        
        # Validate store hours restriction (10 AM - 6 PM)
        from datetime import datetime
        start_time_obj = datetime.strptime(start_time, '%H:%M').time()
        end_time_obj = datetime.strptime(end_time, '%H:%M').time()
        min_time = datetime.strptime('10:00', '%H:%M').time()
        max_time = datetime.strptime('18:00', '%H:%M').time()
        
        if start_time_obj < min_time or end_time_obj > max_time:
            messages.error(request, 'Shift hours must be between 10:00 AM and 6:00 PM.')
            return redirect('owner:manage_attendants')
        
        if start_time_obj >= end_time_obj:
            messages.error(request, 'Start time must be before end time.')
            return redirect('owner:manage_attendants')
        
        # Validate phone number if provided
        if phone:
            import re
            if not re.match(r'^09\d{9}$', phone):
                messages.error(request, 'Phone number must be 11 digits starting with 09 (e.g., 09123456789).')
                return redirect('owner:manage_attendants')
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            profile_picture = request.FILES['profile_picture']
            # Validate file type
            if profile_picture.content_type not in ['image/jpeg', 'image/jpg', 'image/png']:
                messages.error(request, 'Profile picture must be in JPG or PNG format.')
                return redirect('owner:manage_attendants')
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
        
        return redirect('owner:manage_attendants')
    
    return redirect('owner:manage_attendants')


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_add_attendant(request):
    """Add new attendant (owner version) - Note: Attendants are now User objects, use user creation instead"""
    messages.info(request, 'Attendants are now managed as User accounts. Please use the user creation interface.')
    return redirect('owner:manage_attendants')


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_delete_attendant(request, attendant_id):
    """Delete attendant user account (owner version)"""
    attendant = get_object_or_404(User, id=attendant_id, user_type='attendant')
    attendant_name = f"{attendant.first_name} {attendant.last_name}"
    attendant.delete()
    
    messages.success(request, f'Attendant {attendant_name} deleted successfully.')
    return redirect('owner:manage_attendants')


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_add_closed_day(request):
    """Add closed day (owner version)"""
    if request.method == 'POST':
        from appointments.models import ClosedDay
        
        date = request.POST.get('start_date')
        reason = request.POST.get('reason')
        
        if date and reason:
            try:
                ClosedDay.objects.create(date=date, reason=reason)
                messages.success(request, f'Closed day {date} added successfully.')
            except Exception as e:
                messages.error(request, f'Error adding closed day: {str(e)}')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    return redirect('owner:manage_attendants')


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_delete_closed_day(request, closed_day_id):
    """Delete closed day (owner version)"""
    from appointments.models import ClosedDay
    
    closed_day = get_object_or_404(ClosedDay, id=closed_day_id)
    closed_day.delete()
    
    messages.success(request, 'Closed day deleted successfully.')
    return redirect('owner:manage_attendants')


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_add_timeslot(request):
    """Add new time slot (owner version)"""
    from appointments.models import TimeSlot
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
                    return redirect('owner:manage_attendants')
                
                # Check if time slot already exists
                if TimeSlot.objects.filter(time=time_obj).exists():
                    messages.error(request, f'Time slot {time_obj.strftime("%I:%M %p")} already exists')
                    return redirect('owner:manage_attendants')
                
                # Create time slot
                TimeSlot.objects.create(
                    time=time_obj,
                    is_active=is_active
                )
                
                messages.success(request, f'Time slot {time_obj.strftime("%I:%M %p")} added successfully!')
            except ValueError:
                messages.error(request, 'Invalid time format')
        else:
            messages.error(request, 'Time is required')
    
    return redirect('owner:manage_attendants')


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_toggle_timeslot(request, timeslot_id):
    """Toggle time slot active status (owner version)"""
    from appointments.models import TimeSlot
    
    timeslot = get_object_or_404(TimeSlot, id=timeslot_id)
    timeslot.is_active = not timeslot.is_active
    timeslot.save()
    
    new_status = 'Active' if timeslot.is_active else 'Inactive'
    messages.success(request, f'Time slot {timeslot.time.strftime("%I:%M %p")} is now {new_status.lower()}')
    return redirect('owner:manage_attendants')


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_delete_timeslot(request, timeslot_id):
    """Delete time slot (owner version)"""
    from appointments.models import TimeSlot
    
    timeslot = get_object_or_404(TimeSlot, id=timeslot_id)
    time_display = timeslot.time.strftime('%I:%M %p')
    
    timeslot.delete()
    messages.success(request, f'Time slot {time_display} deleted successfully!')
    return redirect('owner:manage_attendants')


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_notifications(request):
    """Owner notifications view - shows all notifications without auto-marking as read"""
    from appointments.models import Notification, CancellationRequest, Appointment
    
    # Show all system notifications (where patient is null) - both read and unread
    notifications = Notification.objects.filter(patient__isnull=True).order_by('-created_at')
    
    # Get cancellation requests for notifications that mention cancellation
    notifications_with_actions = []
    for notification in notifications:
        notification_data = {
            'notification': notification,
            'cancellation_request': None,
            'appointment': None,
        }
        
        # Check if notification is about cancellation and has appointment_id
        if notification.appointment_id and ('cancellation' in notification.title.lower() or 'cancellation' in notification.message.lower()):
            try:
                # Try to find the appointment
                appointment = Appointment.objects.filter(id=notification.appointment_id).first()
                if appointment:
                    notification_data['appointment'] = appointment
                    # Try to find pending cancellation request
                    cancellation_request = CancellationRequest.objects.filter(
                        appointment_id=notification.appointment_id,
                        status='pending'
                    ).first()
                    if cancellation_request:
                        notification_data['cancellation_request'] = cancellation_request
            except Exception:
                pass
        
        notifications_with_actions.append(notification_data)
    
    # Count unread notifications
    unread_count = notifications.filter(is_read=False).count()
    total_count = notifications.count()
    
    # Add pagination
    paginator = Paginator(notifications_with_actions, 25)  # 25 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notifications_with_actions': page_obj,
        'page_obj': page_obj,
        'notifications': notifications,
        'unread_count': unread_count,
        'total_count': total_count,
    }
    
    return render(request, 'owner/notifications.html', context)


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_delete_notification(request, notification_id):
    """Delete notification (owner version)"""
    from appointments.models import Notification
    
    notification = get_object_or_404(Notification, id=notification_id, patient__isnull=True)
    notification.delete()
    
    messages.success(request, 'Notification deleted successfully.')
    return redirect('owner:notifications')


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_mark_notification_read(request, notification_id):
    """Mark notification as read (owner version)"""
    from appointments.models import Notification
    
    notification = get_object_or_404(Notification, id=notification_id, patient__isnull=True)
    notification.is_read = True
    notification.save()
    
    messages.success(request, 'Notification marked as read.')
    return redirect('owner:notifications')


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_approve_cancellation(request, cancellation_request_id):
    """Owner approve cancellation request"""
    from appointments.models import CancellationRequest, Notification, Appointment
    from services.models import HistoryLog
    
    cancellation_request = get_object_or_404(CancellationRequest, id=cancellation_request_id)
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
        HistoryLog.objects.create(
            type='Service',  # Using Service as closest match
            name=f"Cancellation Request #{cancellation_request.id}",
            action='Edited',  # Using Edited as closest match
            performed_by=request.user.get_full_name() or request.user.username,
            details=f'Cancellation approved - Appointment ID: {appointment.id}, Patient: {appointment.patient.full_name}',
            related_id=cancellation_request.id
        )
    else:
        messages.error(request, 'This cancellation request has already been processed.')
    
    return redirect('owner:notifications')


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_reject_cancellation(request, cancellation_request_id):
    """Owner reject cancellation request"""
    from appointments.models import CancellationRequest, Notification, Appointment
    from services.models import HistoryLog
    
    cancellation_request = get_object_or_404(CancellationRequest, id=cancellation_request_id)
    appointment = get_object_or_404(Appointment, id=cancellation_request.appointment_id)
    
    if cancellation_request.status == 'pending':
        # Update cancellation request status
        cancellation_request.status = 'rejected'
        cancellation_request.save()
        
        # Create notification for patient
        Notification.objects.create(
            type='cancellation',
            appointment_id=appointment.id,
            title='Cancellation Rejected',
            message=f'Your cancellation request for {appointment.get_service_name()} on {appointment.appointment_date} at {appointment.appointment_time} has been rejected. Please contact us for more information.',
            patient=appointment.patient
        )
        
        messages.success(request, f'Cancellation request rejected for {appointment.patient.full_name}.')
        
        # Log cancellation rejection
        HistoryLog.objects.create(
            type='Service',  # Using Service as closest match
            name=f"Cancellation Request #{cancellation_request.id}",
            action='Edited',  # Using Edited as closest match
            performed_by=request.user.get_full_name() or request.user.username,
            details=f'Cancellation rejected - Appointment ID: {appointment.id}, Patient: {appointment.patient.full_name}',
            related_id=cancellation_request.id
        )
    else:
        messages.error(request, 'This cancellation request has already been processed.')
    
    return redirect('owner:notifications')


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_manage_clinic_hours(request):
    """Owner manage clinic hours"""
    from accounts.models import StoreHours
    
    if request.method == 'POST':
        # Update store hours for each day
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        performed_by_name = request.user.get_full_name() or request.user.username
        
        for day in days:
            open_time = request.POST.get(f'{day.lower()}_open_time', '')
            close_time = request.POST.get(f'{day.lower()}_close_time', '')
            is_closed = request.POST.get(f'{day.lower()}_closed', '') == 'on'
            
            store_hours, created = StoreHours.objects.get_or_create(
                day_of_week=day,
                defaults={
                    'open_time': open_time if open_time else '09:00:00',
                    'close_time': close_time if close_time else '17:00:00',
                    'is_closed': is_closed
                }
            )
            
            if created:
                # Log new clinic hours entry
                details = f'Open: {store_hours.open_time}, Close: {store_hours.close_time}, Closed: {is_closed}'
                HistoryLog.objects.create(
                    type='Clinic Hours',
                    name=f'{day} Clinic Hours',
                    action='Added',
                    performed_by=performed_by_name,
                    details=details,
                    related_id=store_hours.id
                )
            else:
                # Track changes for logging
                changes = []
                old_open = store_hours.open_time
                old_close = store_hours.close_time
                old_closed = store_hours.is_closed
                
                if open_time and str(old_open) != open_time:
                    changes.append(f'Open time: {old_open} → {open_time}')
                    store_hours.open_time = open_time
                if close_time and str(old_close) != close_time:
                    changes.append(f'Close time: {old_close} → {close_time}')
                    store_hours.close_time = close_time
                if old_closed != is_closed:
                    changes.append(f'Closed status: {old_closed} → {is_closed}')
                    store_hours.is_closed = is_closed
                
                # Only log if there were actual changes
                if changes:
                    store_hours.save()
                    details = '; '.join(changes)
                    HistoryLog.objects.create(
                        type='Clinic Hours',
                        name=f'{day} Clinic Hours',
                        action='Edited',
                        performed_by=performed_by_name,
                        details=details,
                        related_id=store_hours.id
                    )
        
        messages.success(request, 'Clinic hours updated successfully.')
        return redirect('owner:manage_clinic_hours')
    
    # GET request - show current clinic hours
    store_hours = StoreHours.objects.all().order_by('day_of_week')
    store_hours_dict = {sh.day_of_week: sh for sh in store_hours}
    
    # Ensure all days are present
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for day in days:
        if day not in store_hours_dict:
            store_hours_dict[day] = StoreHours(
                day_of_week=day,
                open_time='09:00:00',
                close_time='17:00:00',
                is_closed=(day == 'Sunday')
            )
    
    context = {
        'store_hours': [store_hours_dict[day] for day in days],
    }
    
    return render(request, 'owner/manage_clinic_hours.html', context)


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_backup_database(request):
    """Owner database backup management page"""
    import os
    import subprocess
    from django.conf import settings
    from django.contrib import messages
    from pathlib import Path
    
    backup_dir = Path(settings.BASE_DIR) / 'backups'
    
    # Create backup directory if it doesn't exist
    backup_dir.mkdir(exist_ok=True)
    
    # Handle backup creation
    if request.method == 'POST' and 'create_backup' in request.POST:
        try:
            compress = request.POST.get('compress', 'off') == 'on'
            
            # Call the management command
            cmd = ['python', 'manage.py', 'backup_database', '--output-dir', str(backup_dir)]
            if compress:
                cmd.append('--compress')
            
            result = subprocess.run(
                cmd,
                cwd=settings.BASE_DIR,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                messages.success(request, 'Database backup created successfully!')
            else:
                messages.error(request, f'Backup failed: {result.stderr}')
        except subprocess.TimeoutExpired:
            messages.error(request, 'Backup operation timed out. Please try again.')
        except Exception as e:
            messages.error(request, f'Error creating backup: {str(e)}')
    
    # Handle backup deletion
    if request.method == 'POST' and 'delete_backup' in request.POST:
        backup_filename = request.POST.get('backup_filename')
        if backup_filename:
            backup_path = backup_dir / backup_filename
            if backup_path.exists() and backup_path.is_file():
                try:
                    backup_path.unlink()
                    messages.success(request, f'Backup {backup_filename} deleted successfully.')
                except Exception as e:
                    messages.error(request, f'Error deleting backup: {str(e)}')
            else:
                messages.error(request, 'Backup file not found.')
    
    # Get list of backup files
    backup_files = []
    if backup_dir.exists():
        for file in backup_dir.iterdir():
            if file.is_file() and (file.name.startswith('db_backup_') and 
                                   (file.suffix in ['.sqlite3', '.sql'] or file.suffix == '.gz')):
                file_stat = file.stat()
                backup_files.append({
                    'filename': file.name,
                    'size': file_stat.st_size,
                    'size_mb': round(file_stat.st_size / (1024 * 1024), 2),
                    'created': datetime.fromtimestamp(file_stat.st_mtime),
                    'is_compressed': file.suffix == '.gz',
                })
    
    # Sort by creation time (newest first)
    backup_files.sort(key=lambda x: x['created'], reverse=True)
    
    # Get database info
    db_config = settings.DATABASES['default']
    db_engine = db_config['ENGINE']
    db_name = db_config.get('NAME', 'Unknown')
    
    context = {
        'backup_files': backup_files,
        'backup_dir': backup_dir,
        'db_engine': db_engine,
        'db_name': str(db_name),
        'backup_count': len(backup_files),
    }
    
    return render(request, 'owner/backup_database.html', context)


@login_required(login_url='/accounts/login/owner/')
@user_passes_test(is_owner, login_url='/accounts/login/owner/')
def owner_download_backup(request, filename):
    """Download a backup file"""
    from django.http import FileResponse, Http404
    from django.conf import settings
    from pathlib import Path
    import os
    
    backup_dir = Path(settings.BASE_DIR) / 'backups'
    backup_path = backup_dir / filename
    
    # Security check: ensure file is in backup directory and is a backup file
    if not backup_path.exists() or not backup_path.is_file():
        raise Http404("Backup file not found.")
    
    if not (filename.startswith('db_backup_') and 
            (filename.endswith('.sqlite3') or filename.endswith('.sql') or 
             filename.endswith('.sqlite3.gz') or filename.endswith('.sql.gz'))):
        raise Http404("Invalid backup file.")
    
    # Ensure the file is within the backup directory (prevent directory traversal)
    try:
        backup_path.resolve().relative_to(backup_dir.resolve())
    except ValueError:
        raise Http404("Invalid backup file path.")
    
    response = FileResponse(
        open(backup_path, 'rb'),
        content_type='application/octet-stream'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
