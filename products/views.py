from django.shortcuts import render
from django.core.paginator import Paginator
from .models import Product


def products_list(request):
    """List all products"""
    products = Product.objects.filter(archived=False).order_by('product_name')
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 items per page (4 rows of 3 columns)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'page_obj': page_obj,
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