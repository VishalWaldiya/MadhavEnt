from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory_list, name='inventory_list'),
    path('add-model/', views.add_scooter_model, name='add_scooter_model'),
    path('add-item/', views.add_stock_item, name='add_stock_item'),
]
