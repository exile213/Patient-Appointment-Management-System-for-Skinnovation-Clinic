from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q, Avg
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO

from .models import Payment, StockMovement, UserActivityLog
from appointments.models import Appointment
from accounts.models import User
from products.models import Product
from services.models import Service


def is_owner_or_admin(user):
    return user.is_authenticated and user.user_type in ['owner', 'admin']


@login_required
@user_passes_test(is_owner_or_admin)
def payment_list(request):
    """View all payments"""
    payments = Payment.objects.select_related('appointment', 'appointment__patient').all()
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        payments = payments.filter(payment_status=status_filter)
    
    context = {
        'payments': payments,
        'status_filter': status_filter,
    }
    return render(request, 'payments/payment_list.html', context)


@login_required
@user_passes_test(is_owner_or_admin)
def add_payment(request, appointment_id):
    """Add or update payment for an appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        amount_paid = request.POST.get('amount_paid', 0)
        payment_method = request.POST.get('payment_method')
        payment_status = request.POST.get('payment_status')
        reference_number = request.POST.get('reference_number', '')
        notes = request.POST.get('notes', '')
        
        # Get or create payment
        payment, created = Payment.objects.get_or_create(
            appointment=appointment,
            defaults={
                'amount': amount,
                'amount_paid': amount_paid,
                'payment_status': payment_status,
                'payment_method': payment_method,
                'reference_number': reference_number,
                'notes': notes,
            }
        )
        
        if not created:
            # Update existing payment
            payment.amount = amount
            payment.amount_paid = amount_paid
            payment.payment_status = payment_status
            payment.payment_method = payment_method
            payment.reference_number = reference_number
            payment.notes = notes
            if payment.payment_status == 'paid' and not payment.payment_date:
                payment.payment_date = timezone.now()
            payment.save()
        
        # Log activity
        UserActivityLog.objects.create(
            user=request.user,
            action='create' if created else 'update',
            model_name='Payment',
            object_id=payment.id,
            description=f"{'Added' if created else 'Updated'} payment for appointment {appointment.id}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:200]
        )
        
        messages.success(request, f'Payment {"added" if created else "updated"} successfully!')
        return redirect('appointments:admin_appointment_detail', appointment_id=appointment.id)
    
    # GET request - show payment form
    try:
        payment = Payment.objects.get(appointment=appointment)
    except Payment.DoesNotExist:
        payment = None
    
    # Calculate amount based on service/product/package
    if appointment.service:
        amount = appointment.service.price
    elif appointment.product:
        amount = appointment.product.price * appointment.quantity
    elif appointment.package:
        amount = appointment.package.price
    else:
        amount = 0
    
    context = {
        'appointment': appointment,
        'payment': payment,
        'suggested_amount': amount,
    }
    return render(request, 'payments/add_payment.html', context)


@login_required
@user_passes_test(is_owner_or_admin)
def generate_revenue_report_pdf(request):
    """Generate monthly revenue report as PDF"""
    # Get date range from request or default to current month
    month = request.GET.get('month', timezone.now().month)
    year = request.GET.get('year', timezone.now().year)
    
    try:
        month = int(month)
        year = int(year)
    except:
        month = timezone.now().month
        year = timezone.now().year
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    title = Paragraph(f"Monthly Revenue Report - {datetime(year, month, 1).strftime('%B %Y')}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Get data
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()
    
    # Payments in this month
    payments = Payment.objects.filter(
        payment_date__gte=start_date,
        payment_date__lt=end_date,
        payment_status='paid'
    )
    
    total_revenue = payments.aggregate(total=Sum('amount_paid'))['total'] or 0
    total_transactions = payments.count()
    
    # Summary section
    summary_data = [
        ['Total Revenue:', f'₱{total_revenue:,.2f}'],
        ['Total Transactions:', str(total_transactions)],
        ['Report Generated:', timezone.now().strftime('%B %d, %Y %I:%M %p')],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f7fafc')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Detailed transactions
    if payments.exists():
        elements.append(Paragraph("Transaction Details", styles['Heading2']))
        elements.append(Spacer(1, 0.2*inch))
        
        transaction_data = [['Date', 'Patient', 'Service/Product', 'Amount', 'Method']]
        
        for payment in payments:
            appointment = payment.appointment
            service_name = appointment.get_service_name()
            transaction_data.append([
                payment.payment_date.strftime('%b %d, %Y'),
                appointment.patient.get_full_name(),
                service_name[:30],  # Truncate long names
                f'₱{payment.amount_paid:,.2f}',
                payment.get_payment_method_display() if payment.payment_method else 'N/A'
            ])
        
        transaction_table = Table(transaction_data, colWidths=[1.2*inch, 1.8*inch, 2*inch, 1*inch, 1*inch])
        transaction_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        elements.append(transaction_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Return response
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="revenue_report_{year}_{month:02d}.pdf"'
    
    # Log activity
    UserActivityLog.objects.create(
        user=request.user,
        action='export',
        model_name='Revenue Report',
        description=f'Generated revenue report for {datetime(year, month, 1).strftime("%B %Y")}',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:200]
    )
    
    return response


@login_required
@user_passes_test(is_owner_or_admin)
def generate_patient_history_pdf(request, patient_id):
    """Generate patient history report as PDF"""
    patient = get_object_or_404(User, id=patient_id, user_type='patient')
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    title = Paragraph(f"Patient History Report - {patient.get_full_name()}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.2*inch))
    
    # Patient info
    patient_info = [
        ['Patient Name:', patient.get_full_name()],
        ['Email:', patient.email or 'N/A'],
        ['Phone:', patient.phone or 'N/A'],
        ['Member Since:', patient.created_at.strftime('%B %d, %Y')],
    ]
    
    info_table = Table(patient_info, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f7fafc')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Appointment history
    appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_date')
    
    if appointments.exists():
        elements.append(Paragraph("Appointment History", styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))
        
        appt_data = [['Date', 'Service/Product', 'Status', 'Attendant']]
        
        for appt in appointments[:20]:  # Last 20 appointments
            appt_data.append([
                appt.appointment_date.strftime('%b %d, %Y'),
                appt.get_service_name()[:25],
                appt.get_status_display(),
                f"{appt.attendant.first_name} {appt.attendant.last_name}"[:20]
            ])
        
        appt_table = Table(appt_data, colWidths=[1.3*inch, 2.5*inch, 1.2*inch, 1.5*inch])
        appt_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        elements.append(appt_table)
    else:
        elements.append(Paragraph("No appointment history found.", styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="patient_history_{patient.id}.pdf"'
    
    # Log activity
    UserActivityLog.objects.create(
        user=request.user,
        action='export',
        model_name='Patient History',
        object_id=patient.id,
        description=f'Generated patient history report for {patient.get_full_name()}',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:200]
    )
    
    return response


@login_required
@user_passes_test(is_owner_or_admin)
def stock_movement_list(request):
    """View stock movement history"""
    movements = StockMovement.objects.select_related('product', 'performed_by').all()
    
    # Filter by product
    product_id = request.GET.get('product')
    if product_id:
        movements = movements.filter(product_id=product_id)
    
    # Filter by movement type
    movement_type = request.GET.get('type')
    if movement_type:
        movements = movements.filter(movement_type=movement_type)
    
    products = Product.objects.all()
    
    context = {
        'movements': movements[:100],  # Limit to 100 recent movements
        'products': products,
        'product_filter': product_id,
        'type_filter': movement_type,
    }
    return render(request, 'payments/stock_movement_list.html', context)


@login_required
@user_passes_test(is_owner_or_admin)
def user_activity_log_list(request):
    """View user activity logs"""
    logs = UserActivityLog.objects.select_related('user').all()
    
    # Filter by user
    user_id = request.GET.get('user')
    if user_id:
        logs = logs.filter(user_id=user_id)
    
    # Filter by action
    action = request.GET.get('action')
    if action:
        logs = logs.filter(action=action)
    
    users = User.objects.filter(user_type__in=['admin', 'owner', 'attendant'])
    
    context = {
        'logs': logs[:200],  # Limit to 200 recent logs
        'users': users,
        'user_filter': user_id,
        'action_filter': action,
    }
    return render(request, 'payments/activity_log_list.html', context)


@login_required
@user_passes_test(is_owner_or_admin)
def low_stock_alerts(request):
    """View products with low stock"""
    # Get products with stock below threshold (10 units) - exclude archived products
    low_stock_products = Product.objects.filter(
        stock__lte=10, 
        stock__gt=0,
        archived=False
    ).order_by('stock')
    
    out_of_stock = Product.objects.filter(
        stock=0,
        archived=False
    ).order_by('product_name')
    
    context = {
        'low_stock_products': low_stock_products,
        'out_of_stock': out_of_stock,
    }
    return render(request, 'payments/low_stock_alerts.html', context)
