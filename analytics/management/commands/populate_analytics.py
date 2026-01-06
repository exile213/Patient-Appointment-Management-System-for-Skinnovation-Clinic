from django.core.management.base import BaseCommand
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
from accounts.models import User
from appointments.models import Appointment, Feedback
from services.models import Service
from products.models import Product
from packages.models import Package, PackageBooking
from analytics.models import PatientAnalytics, ServiceAnalytics, BusinessAnalytics, TreatmentCorrelation, PatientSegment
import random
import math


class Command(BaseCommand):
    help = 'Populate analytics data for the beauty clinic'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing analytics data',
        )

    def handle(self, *args, **options):
        self.stdout.write('Starting analytics data population...')
        
        if options['force']:
            self.stdout.write('Force updating existing data...')
            PatientAnalytics.objects.all().delete()
            ServiceAnalytics.objects.all().delete()
            BusinessAnalytics.objects.all().delete()
            TreatmentCorrelation.objects.all().delete()
            PatientSegment.objects.all().delete()
        
        # Populate patient analytics
        self.populate_patient_analytics()
        
        # Populate service analytics
        self.populate_service_analytics()
        
        # Populate business analytics
        self.populate_business_analytics()
        
        # Populate treatment correlations
        self.populate_treatment_correlations()
        
        # Populate patient segments
        self.populate_patient_segments()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated analytics data!')
        )

    def populate_patient_analytics(self):
        """Populate patient analytics data"""
        self.stdout.write('Populating patient analytics...')
        
        patients = User.objects.filter(user_type='patient')
        
        for patient in patients:
            appointments = Appointment.objects.filter(patient=patient)
            completed_appointments = appointments.filter(status='completed')
            
            # Calculate total spent
            total_spent = 0
            for appointment in completed_appointments:
                if appointment.service:
                    total_spent += appointment.service.price
                elif appointment.product:
                    total_spent += appointment.product.price
            
            # Add package spending
            package_spending = PackageBooking.objects.filter(patient=patient).aggregate(
                total=Sum('package__price')
            )['total'] or 0
            total_spent += package_spending
            
            # Calculate average visit frequency
            if completed_appointments.count() > 1:
                first_visit = completed_appointments.order_by('appointment_date').first()
                last_visit = completed_appointments.order_by('-appointment_date').first()
                days_between = (last_visit.appointment_date - first_visit.appointment_date).days
                avg_frequency = days_between / (completed_appointments.count() - 1)
            else:
                avg_frequency = 0
            
            # Get preferred services
            preferred_services = list(
                completed_appointments.filter(service__isnull=False)
                .values_list('service__service_name', flat=True)
                .distinct()[:5]
            )
            
            # Calculate risk score (0-1)
            risk_score = self.calculate_risk_score(patient, completed_appointments)
            
            # Get last visit
            last_visit = completed_appointments.order_by('-appointment_date').first()
            last_visit_date = last_visit.appointment_date if last_visit else None
            
            PatientAnalytics.objects.update_or_create(
                patient=patient,
                defaults={
                    'total_appointments': appointments.count(),
                    'completed_appointments': completed_appointments.count(),
                    'cancelled_appointments': appointments.filter(status='cancelled').count(),
                    'total_spent': total_spent,
                    'last_visit': last_visit_date,
                    'average_visit_frequency': avg_frequency,
                    'preferred_services': preferred_services,
                    'risk_score': risk_score,
                }
            )
        
        self.stdout.write(f'Created/updated {patients.count()} patient analytics records')

    def populate_service_analytics(self):
        """Populate service analytics data"""
        self.stdout.write('Populating service analytics...')
        
        services = Service.objects.all()
        
        for service in services:
            appointments = Appointment.objects.filter(service=service)
            completed_appointments = appointments.filter(status='completed')
            
            # Calculate total revenue
            total_revenue = completed_appointments.aggregate(
                total=Sum('service__price')
            )['total'] or 0
            
            # Calculate average rating
            avg_rating = completed_appointments.filter(
                feedback__isnull=False
            ).aggregate(
                avg=Avg('feedback__rating')
            )['avg'] or 0
            
            # Calculate popularity score (0-1)
            total_services = Service.objects.count()
            service_rank = Service.objects.filter(
                appointments__status='completed'
            ).annotate(
                booking_count=Count('appointments')
            ).order_by('-booking_count').values_list('id', flat=True)
            
            try:
                rank = list(service_rank).index(service.id) + 1
                popularity_score = 1 - (rank - 1) / total_services
            except ValueError:
                popularity_score = 0
            
            # Calculate seasonal trends
            seasonal_trends = {}
            for month in range(1, 13):
                month_appointments = completed_appointments.filter(
                    appointment_date__month=month
                ).count()
                seasonal_trends[str(month)] = month_appointments
            
            ServiceAnalytics.objects.update_or_create(
                service=service,
                defaults={
                    'total_bookings': appointments.count(),
                    'completed_bookings': completed_appointments.count(),
                    'cancelled_bookings': appointments.filter(status='cancelled').count(),
                    'total_revenue': total_revenue,
                    'average_rating': avg_rating,
                    'popularity_score': popularity_score,
                    'seasonal_trends': seasonal_trends,
                }
            )
        
        self.stdout.write(f'Created/updated {services.count()} service analytics records')

    def populate_business_analytics(self):
        """Populate business analytics data"""
        self.stdout.write('Populating business analytics...')
        
        # Generate daily analytics for the last 90 days
        today = timezone.now().date()
        for i in range(90):
            date = today - timedelta(days=i)
            
            # Get appointments for this date
            appointments = Appointment.objects.filter(appointment_date=date)
            completed_appointments = appointments.filter(status='completed')
            
            # Calculate revenue
            total_revenue = 0
            for appointment in completed_appointments:
                if appointment.service:
                    total_revenue += appointment.service.price
                elif appointment.product:
                    total_revenue += appointment.product.price
            
            # Add package revenue
            package_revenue = PackageBooking.objects.filter(
                created_at__date=date
            ).aggregate(
                total=Sum('package__price')
            )['total'] or 0
            total_revenue += package_revenue
            
            # Calculate average appointment value
            avg_appointment_value = (
                total_revenue / completed_appointments.count()
                if completed_appointments.count() > 0 else 0
            )
            
            # Count new patients
            new_patients = User.objects.filter(
                user_type='patient',
                created_at__date=date
            ).count()
            
            # Count returning patients
            returning_patients = User.objects.filter(
                user_type='patient',
                appointments__appointment_date=date
            ).distinct().count()
            
            # Calculate patient satisfaction score
            feedback_ratings = Feedback.objects.filter(
                appointment__appointment_date=date
            ).values_list('rating', flat=True)
            
            patient_satisfaction_score = (
                sum(feedback_ratings) / len(feedback_ratings)
                if feedback_ratings else 0
            )
            
            BusinessAnalytics.objects.update_or_create(
                date=date,
                defaults={
                    'total_appointments': appointments.count(),
                    'completed_appointments': completed_appointments.count(),
                    'cancelled_appointments': appointments.filter(status='cancelled').count(),
                    'new_patients': new_patients,
                    'returning_patients': returning_patients,
                    'total_revenue': total_revenue,
                    'average_appointment_value': avg_appointment_value,
                    'patient_satisfaction_score': patient_satisfaction_score,
                }
            )
        
        self.stdout.write('Created/updated 90 days of business analytics records')

    def populate_treatment_correlations(self):
        """Populate treatment correlation data"""
        self.stdout.write('Populating treatment correlations...')
        
        services = list(Service.objects.all())
        correlations_created = 0
        
        for i, primary_service in enumerate(services):
            for secondary_service in services[i+1:]:
                # Calculate correlation based on patient overlap
                primary_patients = set(
                    Appointment.objects.filter(
                        service=primary_service,
                        status='completed'
                    ).values_list('patient_id', flat=True)
                )
                
                secondary_patients = set(
                    Appointment.objects.filter(
                        service=secondary_service,
                        status='completed'
                    ).values_list('patient_id', flat=True)
                )
                
                # Calculate Jaccard similarity
                intersection = len(primary_patients & secondary_patients)
                union = len(primary_patients | secondary_patients)
                
                if union > 0:
                    correlation_strength = intersection / union
                    
                    # Only create correlations with meaningful strength
                    if correlation_strength >= 0.1:
                        confidence_score = min(1.0, intersection / 10)  # More data = higher confidence
                        
                        TreatmentCorrelation.objects.update_or_create(
                            primary_service=primary_service,
                            secondary_service=secondary_service,
                            defaults={
                                'correlation_strength': correlation_strength,
                                'frequency': intersection,
                                'confidence_score': confidence_score,
                            }
                        )
                        correlations_created += 1
        
        self.stdout.write(f'Created {correlations_created} treatment correlations')

    def populate_patient_segments(self):
        """Populate patient segments"""
        self.stdout.write('Populating patient segments...')
        
        patients = User.objects.filter(user_type='patient')
        segments_created = 0
        
        for patient in patients:
            try:
                analytics = PatientAnalytics.objects.get(patient=patient)
                
                # Determine segment based on analytics
                if analytics.total_spent >= 10000:  # High value threshold
                    segment = 'high_value'
                    segment_score = min(1.0, analytics.total_spent / 20000)
                elif analytics.completed_appointments >= 10:  # Frequent threshold
                    segment = 'frequent'
                    segment_score = min(1.0, analytics.completed_appointments / 20)
                elif analytics.risk_score >= 0.7:  # At risk threshold
                    segment = 'at_risk'
                    segment_score = analytics.risk_score
                elif analytics.completed_appointments <= 2:  # New patient threshold
                    segment = 'new'
                    segment_score = 1.0 - (analytics.completed_appointments / 3)
                else:
                    segment = 'occasional'
                    segment_score = min(1.0, analytics.completed_appointments / 10)
                
                PatientSegment.objects.update_or_create(
                    patient=patient,
                    defaults={
                        'segment': segment,
                        'segment_score': segment_score,
                    }
                )
                segments_created += 1
                
            except PatientAnalytics.DoesNotExist:
                # Create default segment for patients without analytics
                PatientSegment.objects.update_or_create(
                    patient=patient,
                    defaults={
                        'segment': 'new',
                        'segment_score': 1.0,
                    }
                )
                segments_created += 1
        
        self.stdout.write(f'Created {segments_created} patient segments')

    def calculate_risk_score(self, patient, completed_appointments):
        """Calculate churn risk score for a patient"""
        risk_factors = 0
        total_factors = 0
        
        # Factor 1: Time since last visit
        if completed_appointments.exists():
            last_visit = completed_appointments.order_by('-appointment_date').first()
            days_since_last_visit = (timezone.now().date() - last_visit.appointment_date).days
            
            if days_since_last_visit > 90:
                risk_factors += 1
            elif days_since_last_visit > 60:
                risk_factors += 0.5
            total_factors += 1
        
        # Factor 2: Cancellation rate
        total_appointments = Appointment.objects.filter(patient=patient).count()
        cancelled_appointments = Appointment.objects.filter(
            patient=patient,
            status='cancelled'
        ).count()
        
        if total_appointments > 0:
            cancellation_rate = cancelled_appointments / total_appointments
            if cancellation_rate > 0.3:
                risk_factors += 1
            elif cancellation_rate > 0.2:
                risk_factors += 0.5
            total_factors += 1
        
        # Factor 3: Visit frequency decline
        if completed_appointments.count() >= 3:
            recent_appointments = completed_appointments.order_by('-appointment_date')[:3]
            older_appointments = completed_appointments.order_by('-appointment_date')[3:6]
            
            if len(recent_appointments) >= 2 and len(older_appointments) >= 2:
                recent_frequency = self.calculate_visit_frequency(recent_appointments)
                older_frequency = self.calculate_visit_frequency(older_appointments)
                
                if recent_frequency > older_frequency * 1.5:  # Frequency decreased significantly
                    risk_factors += 1
                total_factors += 1
        
        # Factor 4: Low satisfaction (if feedback exists)
        feedback_ratings = Feedback.objects.filter(
            appointment__patient=patient
        ).values_list('rating', flat=True)
        
        if feedback_ratings:
            avg_rating = sum(feedback_ratings) / len(feedback_ratings)
            if avg_rating < 3.0:
                risk_factors += 1
            total_factors += 1
        
        # Calculate final risk score
        if total_factors > 0:
            return min(1.0, risk_factors / total_factors)
        else:
            return 0.0

    def calculate_visit_frequency(self, appointments):
        """Calculate average days between appointments"""
        if len(appointments) < 2:
            return 0
        
        total_days = 0
        for i in range(len(appointments) - 1):
            days_between = (appointments[i].appointment_date - appointments[i + 1].appointment_date).days
            total_days += days_between
        
        return total_days / (len(appointments) - 1)
