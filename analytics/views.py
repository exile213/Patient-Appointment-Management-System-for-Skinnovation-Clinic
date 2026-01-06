from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q, Max
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import PatientAnalytics, ServiceAnalytics, BusinessAnalytics, TreatmentCorrelation, PatientSegment
from accounts.models import User
from appointments.models import Appointment, Feedback
from services.models import Service
from products.models import Product
from packages.models import Package


def is_owner_or_admin(user):
    """Check if user is owner or admin"""
    return user.is_authenticated and user.user_type in ['owner', 'admin']


def is_owner(user):
    """Check if user is owner only"""
    return user.is_authenticated and user.user_type == 'owner'


@login_required
@user_passes_test(is_owner)
def analytics_dashboard(request):
    """Comprehensive analytics dashboard with filtering"""
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
    ).aggregate(total=Sum('service__price'))['total'] or 0
    
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
    from accounts.models import User
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
    
    # For staff (admin) users, use the staff analytics layout with sidebar
    if request.user.is_authenticated and getattr(request.user, 'user_type', '') == 'admin':
        return render(request, 'analytics/admin_dashboard.html', context)

    return render(request, 'analytics/dashboard.html', context)


@login_required
@user_passes_test(is_owner)
def analytics_api(request):
    """API endpoint for real-time analytics data"""
    # Get ALL filter parameters - support both date_range and time_period
    date_range = request.GET.get('date_range', '')
    time_period = request.GET.get('time_period', '')
    status_filter = request.GET.get('status', '')
    service_type_filter = request.GET.get('service_type', '')
    attendant_filter = request.GET.get('attendant', '')
    patient_search = request.GET.get('patient_search', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # Calculate date range based on time_period (owner) or date_range (analytics)
    today = timezone.now().date()
    
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
    elif time_period:
        # Preset time periods from owner dashboard
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
    elif date_range:
        # Legacy date_range parameter from analytics dashboard
        if date_range == '7':
            filter_start_date = today - timedelta(days=7)
        elif date_range == '90':
            filter_start_date = today - timedelta(days=90)
        elif date_range == '365':
            filter_start_date = today - timedelta(days=365)
        else:
            filter_start_date = today - timedelta(days=30)
        filter_end_date = today
    else:
        # Default to last 3 months
        filter_start_date = today - timedelta(days=90)
        filter_end_date = today
    
    # Use custom date range if provided (overrides everything)
    if start_date:
        try:
            filter_start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if end_date:
        try:
            filter_end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Base queryset with ALL filters applied
    # Note: Include future appointments in the chart for visibility
    appointments_qs = Appointment.objects.filter(
        appointment_date__gte=filter_start_date
        # Removed filter_end_date filter to include future appointments
    )
    
    # Apply status filter
    if status_filter:
        appointments_qs = appointments_qs.filter(status=status_filter)
    
    # Apply service type filter
    if service_type_filter == 'service':
        appointments_qs = appointments_qs.exclude(service__isnull=True)
    elif service_type_filter == 'product':
        appointments_qs = appointments_qs.exclude(product__isnull=True)
    elif service_type_filter == 'package':
        appointments_qs = appointments_qs.exclude(package__isnull=True)
    
    # Apply attendant filter
    if attendant_filter:
        appointments_qs = appointments_qs.filter(attendant_id=attendant_filter)
    
    # Apply patient search filter
    if patient_search:
        appointments_qs = appointments_qs.filter(
            Q(patient__first_name__icontains=patient_search) |
            Q(patient__last_name__icontains=patient_search) |
            Q(patient__email__icontains=patient_search)
        )
    
    # Get monthly data for line chart with ACCURATE revenue calculation
    # Monthly grouping is cleaner and more readable than daily
    monthly_data = appointments_qs.annotate(
        month=TruncMonth('appointment_date')
    ).values('month').annotate(
        appointments=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        # Calculate revenue from ALL sources: services, products, packages
        service_revenue=Sum('service__price', filter=Q(status='completed')),
        product_revenue=Sum('product__price', filter=Q(status='completed')),
        package_revenue=Sum('package__price', filter=Q(status='completed'))
    ).order_by('month')
    
    # Create a dictionary of existing data
    data_dict = {}
    for item in monthly_data:
        if item['month']:
            total_revenue = (
                (item['service_revenue'] or 0) +
                (item['product_revenue'] or 0) +
                (item['package_revenue'] or 0)
            )
            data_dict[item['month']] = {
                'appointments': item['appointments'] or 0,
                'completed': item['completed'] or 0,
                'revenue': float(total_revenue),
            }
    
    # Fill in ALL months in the date range (including months with zero appointments)
    chart_data = []
    current_month = filter_start_date.replace(day=1)
    end_month = filter_end_date.replace(day=1)
    
    while current_month <= end_month:
        # Format as "Jan 2026" for better readability
        month_str = current_month.strftime('%b %Y')
        
        if current_month in data_dict:
            chart_data.append({
                'name': month_str,
                **data_dict[current_month]
            })
        else:
            # Add zero values for months with no appointments
            chart_data.append({
                'name': month_str,
                'appointments': 0,
                'completed': 0,
                'revenue': 0,
            })
        
        # Move to next month
        if current_month.month == 12:
            current_month = current_month.replace(year=current_month.year + 1, month=1)
        else:
            current_month = current_month.replace(month=current_month.month + 1)
    
    return JsonResponse({
        'data': chart_data,
        'date_range': date_range,
        'filters_applied': {
            'status': status_filter,
            'service_type': service_type_filter,
            'attendant': attendant_filter,
            'patient_search': patient_search,
        }
    })


@login_required
@user_passes_test(is_owner)
def patient_analytics(request):
    """Detailed patient analytics"""
    # Get filter parameters
    segment_filter = request.GET.get('segment', '')
    search_query = request.GET.get('search', '')
    
    # Get patients with analytics - optimized with prefetch_related
    patients = User.objects.filter(user_type='patient').prefetch_related(
        'analytics', 'segments', 'appointments', 'appointments__service'
    )
    
    # Apply filters
    if segment_filter:
        patients = patients.filter(segments__segment=segment_filter)
    
    if search_query:
        patients = patients.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Calculate analytics for each patient - optimized to avoid N+1 queries
    patient_analytics_list = []
    for patient in patients[:100]:  # Limit to 100 patients for performance
        appointments = patient.appointments.all()
        completed_appointments = [a for a in appointments if a.status == 'completed']
        
        analytics_data = {
            'patient': patient,
            'total_appointments': len(appointments),
            'completed_appointments': len(completed_appointments),
            'cancelled_appointments': len([a for a in appointments if a.status == 'cancelled']),
            'total_spent': sum([app.service.price for app in completed_appointments if app.service and app.service.price]),
            'last_visit': max([a.appointment_date for a in completed_appointments], default=None),
            'segment': patient.segments.first().segment if patient.segments.exists() else 'unclassified',
        }
        patient_analytics_list.append(analytics_data)
    
    # Sort by total spent
    patient_analytics_list.sort(key=lambda x: x['total_spent'], reverse=True)
    
    context = {
        'patient_analytics': patient_analytics_list,
        'segment_filter': segment_filter,
        'search_query': search_query,
    }
    
    return render(request, 'analytics/patient_analytics.html', context)


@login_required
@user_passes_test(is_owner)
def service_analytics(request):
    """Service performance analytics"""
    # Service performance metrics
    services = Service.objects.annotate(
        total_bookings=Count('appointments'),
        completed_bookings=Count('appointments', filter=Q(appointments__status='completed')),
        cancelled_bookings=Count('appointments', filter=Q(appointments__status='cancelled')),
        total_revenue=Sum('appointments__service__price', filter=Q(appointments__status='completed')),
        avg_rating=Avg('appointments__feedback__rating', filter=Q(appointments__feedback__isnull=False))
    ).order_by('-total_bookings')
    
    # Service categories performance
    category_stats = Service.objects.values('category__name').annotate(
        service_count=Count('id'),
        total_bookings=Count('appointments'),
        total_revenue=Sum('appointments__service__price', filter=Q(appointments__status='completed'))
    ).order_by('-total_revenue')
    
    # Seasonal trends
    seasonal_data = Appointment.objects.filter(
        appointment_date__gte=timezone.now().date() - timedelta(days=365)
    ).annotate(
        month=Extract('appointment_date', 'month')
    ).values('month').annotate(
        count=Count('id'),
        revenue=Sum('service__price')
    ).order_by('month')
    
    context = {
        'services': services,
        'category_stats': category_stats,
        'seasonal_data': seasonal_data,
    }
    
    return render(request, 'analytics/service_analytics.html', context)


@login_required
@user_passes_test(is_owner)
def treatment_correlations(request):
    """Treatment correlation analysis"""
    correlations = TreatmentCorrelation.objects.select_related(
        'primary_service', 'secondary_service'
    ).order_by('-correlation_strength')
    
    # Filter by strength
    min_strength = request.GET.get('min_strength', 0.3)
    correlations = correlations.filter(correlation_strength__gte=min_strength)
    
    context = {
        'correlations': correlations,
        'min_strength': min_strength,
    }
    
    return render(request, 'analytics/treatment_correlations.html', context)


@login_required
@user_passes_test(is_owner)
def business_insights(request):
    """Business insights and recommendations"""
    # Calculate key metrics
    total_patients = User.objects.filter(user_type='patient').count()
    total_appointments = Appointment.objects.count()
    completed_appointments = Appointment.objects.filter(status='completed').count()
    cancellation_rate = (Appointment.objects.filter(status='cancelled').count() / total_appointments * 100) if total_appointments > 0 else 0
    
    # Revenue trends
    revenue_trend = Appointment.objects.filter(
        status='completed',
        appointment_date__gte=timezone.now().date() - timedelta(days=90)
    ).annotate(
        week=TruncWeek('appointment_date')
    ).values('week').annotate(
        revenue=Sum('service__price')
    ).order_by('week')
    
    # Patient retention
    retention_data = []
    for i in range(1, 13):  # Last 12 months
        month_start = timezone.now().date().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        
        new_patients = User.objects.filter(
            user_type='patient',
            created_at__gte=month_start,
            created_at__lt=month_end
        ).count()
        
        returning_patients = User.objects.filter(
            user_type='patient',
            appointments__appointment_date__gte=month_start,
            appointments__appointment_date__lt=month_end
        ).distinct().count()
        
        retention_data.append({
            'month': month_start.strftime('%Y-%m'),
            'new_patients': new_patients,
            'returning_patients': returning_patients,
            'retention_rate': (returning_patients / new_patients * 100) if new_patients > 0 else 0
        })
    
    # Generate insights
    insights = []
    
    if cancellation_rate > 20:
        insights.append({
            'type': 'warning',
            'title': 'High Cancellation Rate',
            'message': f'Your cancellation rate is {cancellation_rate:.1f}%. Consider improving appointment reminders and customer service.',
        })
    
    if completed_appointments < total_appointments * 0.7:
        insights.append({
            'type': 'info',
            'title': 'Appointment Completion Rate',
            'message': f'Your completion rate is {(completed_appointments/total_appointments*100):.1f}%. Focus on reducing cancellations.',
        })
    
    # Top performing services
    top_services = Service.objects.annotate(
        booking_count=Count('appointments', filter=Q(appointments__status='completed'))
    ).order_by('-booking_count')[:3]
    
    if top_services:
        insights.append({
            'type': 'success',
            'title': 'Top Performing Services',
            'message': f'Your most popular services are: {", ".join([s.service_name for s in top_services])}. Consider promoting these further.',
        })
    
    context = {
        'total_patients': total_patients,
        'total_appointments': total_appointments,
        'completed_appointments': completed_appointments,
        'cancellation_rate': cancellation_rate,
        'revenue_trend': revenue_trend,
        'retention_data': retention_data,
        'insights': insights,
    }
    
    return render(request, 'analytics/business_insights.html', context)


@login_required
@user_passes_test(is_owner)
def feedback_analytics(request):
    """Feedback analytics dashboard with rating trends and sentiment analysis"""
    # Get date range
    date_range = request.GET.get('date_range', '30')
    today = timezone.now().date()
    
    if date_range == '7':
        start_date = today - timedelta(days=7)
    elif date_range == '90':
        start_date = today - timedelta(days=90)
    elif date_range == '365':
        start_date = today - timedelta(days=365)
    else:
        start_date = today - timedelta(days=30)
    
    # Get feedback data
    feedbacks = Feedback.objects.filter(
        created_at__gte=start_date
    ).select_related('appointment', 'appointment__patient', 'appointment__service', 'appointment__attendant')
    
    # Overall statistics
    total_feedbacks = feedbacks.count()
    avg_rating = feedbacks.aggregate(Avg('rating'))['rating__avg'] or 0
    avg_attendant_rating = feedbacks.aggregate(Avg('attendant_rating'))['attendant_rating__avg'] or 0
    
    # Rating distribution
    rating_distribution = feedbacks.values('rating').annotate(count=Count('id')).order_by('rating')
    attendant_rating_distribution = feedbacks.values('attendant_rating').annotate(count=Count('id')).order_by('attendant_rating')
    
    # Service quality by rating
    service_ratings = feedbacks.filter(
        appointment__service__isnull=False
    ).values(
        'appointment__service__service_name'
    ).annotate(
        avg_rating=Avg('rating'),
        count=Count('id')
    ).order_by('-avg_rating')[:10]
    
    # Attendant performance
    attendant_performance = feedbacks.values(
        'appointment__attendant__first_name',
        'appointment__attendant__last_name'
    ).annotate(
        avg_service_rating=Avg('rating'),
        avg_attendant_rating=Avg('attendant_rating'),
        total_feedbacks=Count('id')
    ).order_by('-avg_attendant_rating')[:10]
    
    # Rating trends over time
    rating_trends = feedbacks.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        avg_rating=Avg('rating'),
        count=Count('id')
    ).order_by('month')
    
    # Sentiment analysis (simple implementation based on ratings and comments)
    positive_feedback = feedbacks.filter(rating__gte=4).count()
    neutral_feedback = feedbacks.filter(rating=3).count()
    negative_feedback = feedbacks.filter(rating__lte=2).count()
    
    sentiment_percentage = {
        'positive': round((positive_feedback / total_feedbacks * 100), 1) if total_feedbacks > 0 else 0,
        'neutral': round((neutral_feedback / total_feedbacks * 100), 1) if total_feedbacks > 0 else 0,
        'negative': round((negative_feedback / total_feedbacks * 100), 1) if total_feedbacks > 0 else 0,
    }
    
    # Recent feedback with comments
    recent_feedback = feedbacks.filter(
        comments__isnull=False
    ).exclude(comments='').order_by('-created_at')[:10]
    
    context = {
        'total_feedbacks': total_feedbacks,
        'avg_rating': round(avg_rating, 2),
        'avg_attendant_rating': round(avg_attendant_rating, 2),
        'rating_distribution': list(rating_distribution),
        'attendant_rating_distribution': list(attendant_rating_distribution),
        'service_ratings': list(service_ratings),
        'attendant_performance': list(attendant_performance),
        'rating_trends': list(rating_trends),
        'positive_feedback': positive_feedback,
        'neutral_feedback': neutral_feedback,
        'negative_feedback': negative_feedback,
        'sentiment_percentage': sentiment_percentage,
        'recent_feedback': recent_feedback,
        'date_range': date_range,
    }
    
    return render(request, 'analytics/feedback_analytics.html', context)
