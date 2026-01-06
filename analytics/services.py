from django.db.models import Count, Sum, Avg, Q, F, Case, When, IntegerField
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay, Extract
from django.utils import timezone
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
from accounts.models import User
from appointments.models import Appointment, Feedback
from services.models import Service
from products.models import Product
from packages.models import Package, PackageBooking
from .models import PatientAnalytics, ServiceAnalytics, BusinessAnalytics, TreatmentCorrelation, PatientSegment


class AnalyticsService:
    """Comprehensive analytics service for business insights"""
    
    def __init__(self):
        self.today = timezone.now().date()
        self.last_30_days = self.today - timedelta(days=30)
        self.last_90_days = self.today - timedelta(days=90)
        self.last_year = self.today - timedelta(days=365)
    
    def get_business_overview(self):
        """Get comprehensive business overview metrics"""
        total_patients = User.objects.filter(user_type='patient').count()
        total_appointments = Appointment.objects.count()
        completed_appointments = Appointment.objects.filter(status='completed').count()
        cancelled_appointments = Appointment.objects.filter(status='cancelled').count()
        
        # Revenue calculations
        service_revenue = Appointment.objects.filter(
            status='completed',
            service__isnull=False
        ).aggregate(total=Sum('service__price'))['total'] or 0
        
        product_revenue = Appointment.objects.filter(
            status='completed',
            product__isnull=False
        ).aggregate(total=Sum('product__price'))['total'] or 0
        
        package_revenue = PackageBooking.objects.aggregate(
            total=Sum('package__price')
        )['total'] or 0
        
        total_revenue = service_revenue + product_revenue + package_revenue
        
        # Key performance indicators
        completion_rate = (completed_appointments / total_appointments * 100) if total_appointments > 0 else 0
        cancellation_rate = (cancelled_appointments / total_appointments * 100) if total_appointments > 0 else 0
        avg_appointment_value = (total_revenue / completed_appointments) if completed_appointments > 0 else 0
        
        # Recent performance (last 30 days)
        recent_appointments = Appointment.objects.filter(
            appointment_date__gte=self.last_30_days
        ).count()
        
        recent_revenue = Appointment.objects.filter(
            status='completed',
            appointment_date__gte=self.last_30_days
        ).aggregate(
            total=Sum(
                Case(
                    When(service__isnull=False, then='service__price'),
                    When(product__isnull=False, then='product__price'),
                    default=0,
                    output_field=IntegerField()
                )
            )
        )['total'] or 0
        
        # Patient growth
        new_patients_30_days = User.objects.filter(
            user_type='patient',
            created_at__gte=self.last_30_days
        ).count()
        
        active_patients = User.objects.filter(
            user_type='patient',
            appointments__appointment_date__gte=self.last_30_days
        ).distinct().count()
        
        # Calculate pending appointments
        pending_appointments = total_appointments - completed_appointments - cancelled_appointments
        
        return {
            'total_patients': total_patients,
            'total_appointments': total_appointments,
            'completed_appointments': completed_appointments,
            'cancelled_appointments': cancelled_appointments,
            'pending_appointments': pending_appointments,
            'total_revenue': total_revenue,
            'service_revenue': service_revenue,
            'product_revenue': product_revenue,
            'package_revenue': package_revenue,
            'completion_rate': completion_rate,
            'cancellation_rate': cancellation_rate,
            'avg_appointment_value': avg_appointment_value,
            'recent_appointments': recent_appointments,
            'recent_revenue': recent_revenue,
            'new_patients_30_days': new_patients_30_days,
            'active_patients': active_patients,
        }
    
    def get_revenue_analytics(self):
        """Get detailed revenue analytics with trends"""
        # Daily revenue for last 30 days
        daily_revenue = Appointment.objects.filter(
            status='completed',
            appointment_date__gte=self.last_30_days
        ).annotate(
            day=TruncDay('appointment_date')
        ).values('day').annotate(
            revenue=Sum(
                Case(
                    When(service__isnull=False, then='service__price'),
                    When(product__isnull=False, then='product__price'),
                    default=0,
                    output_field=IntegerField()
                )
            )
        ).order_by('day')
        
        # Monthly revenue for last 12 months
        monthly_revenue = Appointment.objects.filter(
            status='completed',
            appointment_date__gte=self.last_year
        ).annotate(
            month=TruncMonth('appointment_date')
        ).values('month').annotate(
            revenue=Sum(
                Case(
                    When(service__isnull=False, then='service__price'),
                    When(product__isnull=False, then='product__price'),
                    default=0,
                    output_field=IntegerField()
                )
            ),
            appointments=Count('id')
        ).order_by('month')
        
        # Revenue by service category
        category_revenue = Service.objects.values('category__name').annotate(
            revenue=Sum('appointments__service__price', filter=Q(appointments__status='completed')),
            bookings=Count('appointments', filter=Q(appointments__status='completed'))
        ).filter(revenue__isnull=False).order_by('-revenue')
        
        # Revenue trends and growth
        monthly_revenue_list = list(monthly_revenue)
        current_month_revenue = sum([item['revenue'] for item in monthly_revenue_list[-1:]]) if monthly_revenue_list else 0
        previous_month_revenue = sum([item['revenue'] for item in monthly_revenue_list[-2:-1]]) if len(monthly_revenue_list) > 1 else 0
        
        revenue_growth = ((current_month_revenue - previous_month_revenue) / previous_month_revenue * 100) if previous_month_revenue > 0 else 0
        
        return {
            'daily_revenue': list(daily_revenue),
            'monthly_revenue': monthly_revenue_list,
            'category_revenue': list(category_revenue),
            'revenue_growth': revenue_growth,
            'current_month_revenue': current_month_revenue,
            'previous_month_revenue': previous_month_revenue,
        }
    
    def get_patient_analytics(self):
        """Get comprehensive patient analytics"""
        # Patient segments
        segments = PatientSegment.objects.values('segment').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Patient lifetime value analysis
        patient_lifetime_values = []
        for patient in User.objects.filter(user_type='patient'):
            appointments = Appointment.objects.filter(patient=patient, status='completed')
            total_spent = sum([
                app.service.price if app.service else 
                app.product.price if app.product else 0
                for app in appointments
            ])
            
            # Add package spending
            package_spending = PackageBooking.objects.filter(patient=patient).aggregate(
                total=Sum('package__price')
            )['total'] or 0
            
            total_spent += package_spending
            
            patient_lifetime_values.append({
                'patient': patient,
                'total_spent': total_spent,
                'appointment_count': appointments.count(),
                'first_visit': appointments.order_by('appointment_date').first(),
                'last_visit': appointments.order_by('-appointment_date').first(),
                'avg_visit_value': total_spent / appointments.count() if appointments.count() > 0 else 0,
            })
        
        # Sort by total spent
        patient_lifetime_values.sort(key=lambda x: x['total_spent'], reverse=True)
        
        # Patient retention analysis
        retention_data = []
        for i in range(1, 13):  # Last 12 months
            month_start = self.today.replace(day=1) - timedelta(days=30*i)
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
            
            retention_rate = (returning_patients / new_patients * 100) if new_patients > 0 else 0
            
            retention_data.append({
                'month': month_start.strftime('%Y-%m'),
                'new_patients': new_patients,
                'returning_patients': returning_patients,
                'retention_rate': retention_rate
            })
        
        # Patient demographics
        demographics = {
            'gender': User.objects.filter(user_type='patient').values('gender').annotate(
                count=Count('id')
            ).order_by('-count'),
            'age_groups': self._get_age_groups(),
        }
        
        return {
            'segments': list(segments),
            'patient_lifetime_values': patient_lifetime_values[:20],  # Top 20
            'retention_data': retention_data,
            'demographics': demographics,
        }
    
    def get_service_analytics(self):
        """Get comprehensive service performance analytics"""
        # Service performance metrics
        services = Service.objects.annotate(
            total_bookings=Count('appointments'),
            completed_bookings=Count('appointments', filter=Q(appointments__status='completed')),
            cancelled_bookings=Count('appointments', filter=Q(appointments__status='cancelled')),
            total_revenue=Sum('appointments__service__price', filter=Q(appointments__status='completed')),
            avg_rating=Avg('appointments__feedback__rating', filter=Q(appointments__feedback__isnull=False)),
            conversion_rate=Case(
                When(total_bookings=0, then=0),
                default=F('completed_bookings') * 100.0 / F('total_bookings'),
                output_field=IntegerField()
            )
        ).order_by('-total_revenue')
        
        # Service categories performance
        category_performance = Service.objects.values('category__name').annotate(
            service_count=Count('id'),
            total_bookings=Count('appointments'),
            completed_bookings=Count('appointments', filter=Q(appointments__status='completed')),
            total_revenue=Sum('appointments__service__price', filter=Q(appointments__status='completed')),
            avg_rating=Avg('appointments__feedback__rating', filter=Q(appointments__feedback__isnull=False))
        ).order_by('-total_revenue')
        
        # Seasonal trends
        seasonal_data = Appointment.objects.filter(
            appointment_date__gte=self.last_year
        ).annotate(
            month=Extract('appointment_date', 'month')
        ).values('month').annotate(
            count=Count('id'),
            revenue=Sum('service__price', filter=Q(status='completed'))
        ).order_by('month')
        
        # Service popularity trends
        popularity_trends = []
        services_list = list(services)
        for service in services_list[:10]:  # Top 10 services
            monthly_bookings = Appointment.objects.filter(
                service=service,
                appointment_date__gte=self.last_year
            ).annotate(
                month=TruncMonth('appointment_date')
            ).values('month').annotate(
                bookings=Count('id')
            ).order_by('month')
            
            popularity_trends.append({
                'service': service,
                'monthly_bookings': list(monthly_bookings)
            })
        
        return {
            'services': services_list,
            'category_performance': list(category_performance),
            'seasonal_data': list(seasonal_data),
            'popularity_trends': popularity_trends,
        }
    
    def get_treatment_correlations(self):
        """Get treatment correlation analysis"""
        correlations = TreatmentCorrelation.objects.select_related(
            'primary_service', 'secondary_service'
        ).order_by('-correlation_strength')
        
        # Strong correlations (>= 0.5)
        strong_correlations = correlations.filter(correlation_strength__gte=0.5)
        
        # Weak correlations (0.3 - 0.5)
        weak_correlations = correlations.filter(
            correlation_strength__gte=0.3,
            correlation_strength__lt=0.5
        )
        
        # Negative correlations
        negative_correlations = correlations.filter(correlation_strength__lt=0)
        
        return {
            'strong_correlations': list(strong_correlations),
            'weak_correlations': list(weak_correlations),
            'negative_correlations': list(negative_correlations),
            'all_correlations': list(correlations[:50]),  # Top 50
        }
    
    def get_business_insights(self):
        """Generate actionable business insights and recommendations"""
        overview = self.get_business_overview()
        revenue_data = self.get_revenue_analytics()
        patient_data = self.get_patient_analytics()
        service_data = self.get_service_analytics()
        
        insights = []
        
        # Revenue insights
        if revenue_data['revenue_growth'] < 0:
            insights.append({
                'type': 'warning',
                'category': 'Revenue',
                'title': 'Declining Revenue',
                'message': f'Revenue has decreased by {abs(revenue_data["revenue_growth"]):.1f}% compared to last month. Consider promotional campaigns or new services.',
                'priority': 'high',
                'action': 'Review pricing strategy and marketing efforts'
            })
        elif revenue_data['revenue_growth'] > 20:
            insights.append({
                'type': 'success',
                'category': 'Revenue',
                'title': 'Strong Revenue Growth',
                'message': f'Revenue has increased by {revenue_data["revenue_growth"]:.1f}% compared to last month. Great performance!',
                'priority': 'low',
                'action': 'Maintain current strategies and consider expansion'
            })
        
        # Patient insights
        if overview['cancellation_rate'] > 20:
            insights.append({
                'type': 'warning',
                'category': 'Patients',
                'title': 'High Cancellation Rate',
                'message': f'Your cancellation rate is {overview["cancellation_rate"]:.1f}%. This is above industry average.',
                'priority': 'high',
                'action': 'Implement better appointment reminders and flexible scheduling'
            })
        
        if overview['new_patients_30_days'] < 5:
            insights.append({
                'type': 'warning',
                'category': 'Patients',
                'title': 'Low New Patient Acquisition',
                'message': f'Only {overview["new_patients_30_days"]} new patients in the last 30 days.',
                'priority': 'medium',
                'action': 'Increase marketing efforts and referral programs'
            })
        
        # Service insights
        top_service = service_data['services'][0] if service_data['services'] else None
        if top_service and top_service.total_revenue:
            insights.append({
                'type': 'info',
                'category': 'Services',
                'title': 'Top Performing Service',
                'message': f'{top_service.service_name} generates ₱{top_service.total_revenue:,.2f} in revenue.',
                'priority': 'low',
                'action': 'Consider promoting this service more or creating similar offerings'
            })
        
        # Operational insights
        if overview['completion_rate'] < 70:
            insights.append({
                'type': 'warning',
                'category': 'Operations',
                'title': 'Low Completion Rate',
                'message': f'Your completion rate is {overview["completion_rate"]:.1f}%. Focus on reducing no-shows.',
                'priority': 'medium',
                'action': 'Implement confirmation calls and flexible rescheduling'
            })
        
        # Customer satisfaction insights
        avg_rating = service_data['services'][0].avg_rating if service_data['services'] and service_data['services'][0].avg_rating else 0
        if avg_rating > 0 and avg_rating < 4.0:
            insights.append({
                'type': 'warning',
                'category': 'Satisfaction',
                'title': 'Low Customer Satisfaction',
                'message': f'Average rating is {avg_rating:.1f}/5.0. Focus on service quality.',
                'priority': 'high',
                'action': 'Review service delivery and staff training'
            })
        
        return insights
    
    def _get_age_groups(self):
        """Calculate age groups for patients"""
        age_groups = defaultdict(int)
        
        for patient in User.objects.filter(user_type='patient', birthday__isnull=False):
            if patient.birthday:
                age = (self.today - patient.birthday).days // 365
                if age < 25:
                    age_groups['18-24'] += 1
                elif age < 35:
                    age_groups['25-34'] += 1
                elif age < 45:
                    age_groups['35-44'] += 1
                elif age < 55:
                    age_groups['45-54'] += 1
                elif age < 65:
                    age_groups['55-64'] += 1
                else:
                    age_groups['65+'] += 1
        
        return dict(age_groups)
    
    def get_diagnostic_metrics(self):
        """Get diagnostic metrics for business health"""
        overview = self.get_business_overview()
        
        # Calculate diagnostic scores (0-100)
        completion_score = min(overview['completion_rate'], 100)
        growth_score = max(0, min(100, (overview['new_patients_30_days'] / 10) * 100))  # Target: 10 new patients/month
        retention_score = max(0, min(100, (overview['active_patients'] / overview['total_patients']) * 100)) if overview['total_patients'] > 0 else 0
        revenue_score = max(0, min(100, (overview['recent_revenue'] / 50000) * 100))  # Target: ₱50,000/month
        
        # Overall health score
        overall_score = (completion_score + growth_score + retention_score + revenue_score) / 4
        
        return {
            'overall_score': overall_score,
            'completion_score': completion_score,
            'growth_score': growth_score,
            'retention_score': retention_score,
            'revenue_score': revenue_score,
            'health_status': self._get_health_status(overall_score)
        }
    
    def _get_health_status(self, score):
        """Get health status based on score"""
        if score >= 80:
            return {'status': 'Excellent', 'color': 'success', 'icon': 'fas fa-check-circle'}
        elif score >= 60:
            return {'status': 'Good', 'color': 'info', 'icon': 'fas fa-info-circle'}
        elif score >= 40:
            return {'status': 'Fair', 'color': 'warning', 'icon': 'fas fa-exclamation-triangle'}
        else:
            return {'status': 'Poor', 'color': 'danger', 'icon': 'fas fa-times-circle'}