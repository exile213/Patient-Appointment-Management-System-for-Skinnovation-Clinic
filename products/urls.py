from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.products_list, name='list'),
    path('<int:product_id>/', views.product_detail, name='detail'),
]
