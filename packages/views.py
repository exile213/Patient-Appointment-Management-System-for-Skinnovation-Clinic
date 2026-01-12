from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Package, PackageBooking, PackageAppointment


def packages_list(request):
    """List all packages with filtering"""
    # Get filter parameters
    price_filter = request.GET.get('price', '')
    category_filter = request.GET.get('category', '')
    sessions_filter = request.GET.get('sessions', '')
    
    packages = Package.objects.filter(archived=False).order_by('package_name')
    
    # Apply price filter
    if price_filter:
        if price_filter == 'under_2000':
            packages = packages.filter(price__lt=2000)
        elif price_filter == '2000_3000':
            packages = packages.filter(price__gte=2000, price__lt=3000)
        elif price_filter == '3000_4000':
            packages = packages.filter(price__gte=3000, price__lt=4000)
        elif price_filter == 'over_4000':
            packages = packages.filter(price__gte=4000)
    
    # Apply category filter
    if category_filter:
        if category_filter == 'whitening':
            packages = packages.filter(package_name__icontains='whitening')
        elif category_filter == 'ipl':
            packages = packages.filter(package_name__icontains='IPL')
        elif category_filter == 'facial':
            packages = packages.filter(package_name__icontains='facial')
        elif category_filter == 'cavitation':
            packages = packages.filter(package_name__icontains='cavitation')
        elif category_filter == 'laser':
            packages = packages.filter(package_name__icontains='laser')
        elif category_filter == 'infusion':
            packages = packages.filter(package_name__icontains='infusion')
    
    # Apply sessions filter
    if sessions_filter:
        if sessions_filter == '1_3':
            packages = packages.filter(sessions__gte=1, sessions__lte=3)
        elif sessions_filter == '4_6':
            packages = packages.filter(sessions__gte=4, sessions__lte=6)
        elif sessions_filter == '7_10':
            packages = packages.filter(sessions__gte=7, sessions__lte=10)
        elif sessions_filter == 'over_10':
            packages = packages.filter(sessions__gt=10)
    
    # Pagination - only for unfiltered results
    page_obj = None
    if not price_filter and not category_filter and not sessions_filter:
        paginator = Paginator(packages, 12)  # 12 items per page (4 rows of 3 columns)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        packages = page_obj  # Use page_obj for template
    
    # Get query parameters for pagination
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    
    context = {
        'packages': packages,
        'page_obj': page_obj,
        'price_filter': price_filter,
        'category_filter': category_filter,
        'sessions_filter': sessions_filter,
        'query_params': query_params,
    }
    
    return render(request, 'packages/packages_list.html', context)


def package_detail(request, package_id):
    """Package detail view"""
    package = get_object_or_404(Package, id=package_id)
    
    context = {
        'package': package,
    }
    
    return render(request, 'packages/package_detail.html', context)


@login_required
def my_packages(request):
    """User's package bookings"""
    bookings = PackageBooking.objects.filter(patient=request.user).order_by('-created_at')
    
    context = {
        'bookings': bookings,
    }
    
    return render(request, 'packages/my_packages.html', context)