from django.urls import path
from . import views

app_name = 'packages'

urlpatterns = [
    path('', views.packages_list, name='list'),
    path('<int:package_id>/', views.package_detail, name='detail'),
    path('my-packages/', views.my_packages, name='my_packages'),
]
