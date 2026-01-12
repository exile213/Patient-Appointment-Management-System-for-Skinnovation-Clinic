from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Service, ServiceCategory
from .forms import ServiceForm


def is_admin_or_owner(user):
    """Check if user is staff (admin) or owner"""
    return user.is_authenticated and user.user_type in ['admin', 'owner']


def services_list(request):
    """List all services with optional category, price, and duration filtering"""
    category_id = request.GET.get('category')
    price_filter = request.GET.get('price', '')
    duration_filter = request.GET.get('duration', '')
    
    services = Service.objects.filter(archived=False).order_by('service_name')
    
    # Apply category filter
    if category_id:
        services = services.filter(category_id=category_id)
        category = get_object_or_404(ServiceCategory, id=category_id)
    else:
        category = None
    
    # Apply price filter
    if price_filter:
        if price_filter == 'under_500':
            services = services.filter(price__lt=500)
        elif price_filter == '500_1000':
            services = services.filter(price__gte=500, price__lt=1000)
        elif price_filter == '1000_2000':
            services = services.filter(price__gte=1000, price__lt=2000)
        elif price_filter == 'over_2000':
            services = services.filter(price__gte=2000)
    
    # Apply duration filter
    if duration_filter:
        if duration_filter == 'under_30':
            services = services.filter(duration__lt=30)
        elif duration_filter == '30_60':
            services = services.filter(duration__gte=30, duration__lt=60)
        elif duration_filter == '60_90':
            services = services.filter(duration__gte=60, duration__lt=90)
        elif duration_filter == 'over_90':
            services = services.filter(duration__gte=90)
    
    # Pagination - only for unfiltered results
    page_obj = None
    if not category_id and not price_filter and not duration_filter:
        paginator = Paginator(services, 12)  # 12 items per page (4 rows of 3 columns)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        services = page_obj  # Use page_obj for template
    
    categories = ServiceCategory.objects.all()
    
    # Get query parameters for pagination
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    
    context = {
        'services': services,
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category,
        'price_filter': price_filter,
        'duration_filter': duration_filter,
        'query_params': query_params,
    }
    
    return render(request, 'services/services_list.html', context)


def service_detail(request, service_id):
    """Service detail view"""
    service = get_object_or_404(Service, id=service_id)
    
    context = {
        'service': service,
    }
    
    return render(request, 'services/service_detail.html', context)


@login_required
@user_passes_test(is_admin_or_owner)
def upload_service(request):
    """Upload a new service with image - Staff and Owner only"""
    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES)
        if form.is_valid():
            service = form.save()
            messages.success(request, f'Service "{service.service_name}" has been added successfully!')
            return redirect('services:detail', service_id=service.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ServiceForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'services/upload_service.html', context)