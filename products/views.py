from django.shortcuts import render
from django.core.paginator import Paginator
from .models import Product


def products_list(request):
    """List all products with filtering"""
    # Get filter parameters
    price_filter = request.GET.get('price', '')
    stock_filter = request.GET.get('stock', '')
    search_query = request.GET.get('search', '').strip()
    
    products = Product.objects.filter(archived=False).order_by('product_name')
    
    # Apply search filter
    if search_query:
        products = products.filter(product_name__icontains=search_query)
    
    # Apply price filter
    if price_filter:
        if price_filter == 'under_200':
            products = products.filter(price__lt=200)
        elif price_filter == '200_500':
            products = products.filter(price__gte=200, price__lt=500)
        elif price_filter == '500_1000':
            products = products.filter(price__gte=500, price__lt=1000)
        elif price_filter == 'over_1000':
            products = products.filter(price__gte=1000)
    
    # Apply stock filter
    if stock_filter:
        if stock_filter == 'in_stock':
            products = products.filter(stock__gt=5)
        elif stock_filter == 'low_stock':
            products = products.filter(stock__gt=0, stock__lte=5)
        elif stock_filter == 'out_of_stock':
            products = products.filter(stock__lte=0)
    
    # Pagination - only for unfiltered results
    page_obj = None
    if not price_filter and not stock_filter and not search_query:
        paginator = Paginator(products, 12)  # 12 items per page (4 rows of 3 columns)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        products = page_obj  # Use page_obj for template
    
    # Get query parameters for pagination
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    
    context = {
        'products': products,
        'page_obj': page_obj,
        'price_filter': price_filter,
        'stock_filter': stock_filter,
        'search_query': search_query,
        'query_params': query_params,
    }
    
    return render(request, 'products/products_list.html', context)


def product_detail(request, product_id):
    """Product detail view"""
    from django.shortcuts import get_object_or_404
    product = get_object_or_404(Product, id=product_id)
    
    context = {
        'product': product,
    }
    
    return render(request, 'products/product_detail.html', context)