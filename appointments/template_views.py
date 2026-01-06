from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from .models import SMSTemplate
from .forms import SMSTemplateForm
from services.template_service import template_service
import logging

logger = logging.getLogger(__name__)

def is_admin_or_owner(user):
    """Check if user is admin or owner"""
    return user.is_authenticated and user.user_type in ['admin', 'owner']

@login_required
def template_list(request):
    """List all SMS templates"""
    if not is_admin_or_owner(request.user):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    templates = SMSTemplate.objects.all().order_by('template_type', 'name')
    
    # Filter by template type if provided
    template_type = request.GET.get('type')
    if template_type:
        templates = templates.filter(template_type=template_type)
    
    # Pagination
    paginator = Paginator(templates, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'template_types': SMSTemplate.TEMPLATE_TYPE_CHOICES,
        'selected_type': template_type,
    }
    
    return render(request, 'appointments/sms_template_list.html', context)

@login_required
def template_detail(request, template_id):
    """View template details and preview"""
    if not is_admin_or_owner(request.user):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    template = get_object_or_404(SMSTemplate, id=template_id)
    
    # Get available variables for this template type
    available_variables = template.get_available_variables()
    
    # Sample context for preview
    sample_context = {
        'patient_name': 'Juan Dela Cruz',
        'appointment_date': 'December 25, 2024',
        'appointment_time': '2:00 PM',
        'service_name': 'Facial Treatment',
        'package_name': 'Premium Package',
        'package_price': 'P5,000.00',
        'package_sessions': '5',
        'package_duration': '30 days',
        'cancellation_reason': 'Emergency situation',
        'clinic_name': 'Beauty Clinic',
        'clinic_phone': '09123456789',
        'clinic_address': '123 Main Street, City'
    }
    
    # Render preview
    preview_message = template_service.render_template(template, sample_context)
    
    context = {
        'template': template,
        'available_variables': available_variables,
        'preview_message': preview_message,
        'sample_context': sample_context,
    }
    
    return render(request, 'appointments/sms_template_detail.html', context)

@login_required
def template_create(request):
    """Create new SMS template"""
    if not is_admin_or_owner(request.user):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    if request.method == 'POST':
        form = SMSTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            messages.success(request, f'Template "{template.name}" created successfully!')
            return redirect('template_detail', template_id=template.id)
    else:
        form = SMSTemplateForm()
    
    context = {
        'form': form,
        'template_types': SMSTemplate.TEMPLATE_TYPE_CHOICES,
    }
    
    return render(request, 'appointments/sms_template_form.html', context)

@login_required
def template_edit(request, template_id):
    """Edit existing SMS template"""
    if not is_admin_or_owner(request.user):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    template = get_object_or_404(SMSTemplate, id=template_id)
    
    if request.method == 'POST':
        form = SMSTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, f'Template "{template.name}" updated successfully!')
            return redirect('template_detail', template_id=template.id)
    else:
        form = SMSTemplateForm(instance=template)
    
    context = {
        'form': form,
        'template': template,
        'template_types': SMSTemplate.TEMPLATE_TYPE_CHOICES,
    }
    
    return render(request, 'appointments/sms_template_form.html', context)

@login_required
@require_http_methods(["POST"])
def template_toggle_active(request, template_id):
    """Toggle template active status"""
    if not is_admin_or_owner(request.user):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    template = get_object_or_404(SMSTemplate, id=template_id)
    template.is_active = not template.is_active
    template.save()
    
    return JsonResponse({
        'success': True,
        'is_active': template.is_active,
        'message': f'Template "{template.name}" {"activated" if template.is_active else "deactivated"} successfully!'
    })

@login_required
@require_http_methods(["POST"])
def template_delete(request, template_id):
    """Delete SMS template"""
    if not is_admin_or_owner(request.user):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    template = get_object_or_404(SMSTemplate, id=template_id)
    template_name = template.name
    template.delete()
    
    return JsonResponse({
        'success': True,
        'message': f'Template "{template_name}" deleted successfully!'
    })

@login_required
def template_preview(request, template_id):
    """Preview template with custom context"""
    if not is_admin_or_owner(request.user):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    template = get_object_or_404(SMSTemplate, id=template_id)
    
    # Get custom context from request
    context = {}
    for key, value in request.POST.items():
        if key.startswith('context_'):
            var_name = key.replace('context_', '')
            context[var_name] = value
    
    # Render template with custom context
    try:
        preview_message = template_service.render_template(template, context)
        return JsonResponse({
            'success': True,
            'preview': preview_message
        })
    except Exception as e:
        logger.error(f"Error previewing template {template.name}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error rendering template: {str(e)}'
        })

@login_required
def template_test_send(request, template_id):
    """Test send template to a phone number"""
    if not is_admin_or_owner(request.user):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    template = get_object_or_404(SMSTemplate, id=template_id)
    phone = request.POST.get('phone')
    
    if not phone:
        return JsonResponse({'success': False, 'error': 'Phone number is required'})
    
    # Get custom context from request
    context = {}
    for key, value in request.POST.items():
        if key.startswith('context_') and key != 'context_phone':
            var_name = key.replace('context_', '')
            context[var_name] = value
    
    # Send test SMS
    try:
        result = template_service.send_custom_message(phone, template.name, context)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': f'Test SMS sent successfully to {phone}'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Failed to send SMS')
            })
    except Exception as e:
        logger.error(f"Error sending test SMS for template {template.name}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error sending SMS: {str(e)}'
        })
