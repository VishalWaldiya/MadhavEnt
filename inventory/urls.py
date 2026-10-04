from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory_list, name='inventory_list'),
    path('add-model/', views.add_scooter_model, name='add_scooter_model'),
    path('add-scooter/', views.add_scooter, name='add_scooter'),
    path('add-battery/', views.add_battery, name='add_battery'),
    path('add-charger/', views.add_charger, name='add_charger'),
    path('add-spare-part/', views.add_spare_part, name='add_spare_part'),
    path('model/<int:model_id>/delete/', views.delete_scooter_model, name='delete_scooter_model'),
    path('model/<int:model_id>/edit/', views.edit_scooter_model, name='edit_scooter_model'),
    path('scooter/<int:item_id>/delete/', views.delete_scooter, name='delete_scooter'),
    path('scooter/<int:item_id>/edit/', views.edit_scooter, name='edit_scooter'),
    path('battery/<int:item_id>/delete/', views.delete_battery, name='delete_battery'),
    path('battery/<int:item_id>/edit/', views.edit_battery, name='edit_battery'),
    path('charger/<int:item_id>/delete/', views.delete_charger, name='delete_charger'),
    path('charger/<int:item_id>/edit/', views.edit_charger, name='edit_charger'),
    path('spare-part/<int:item_id>/delete/', views.delete_spare_part, name='delete_spare_part'),
    path('spare-part/<int:item_id>/edit/', views.edit_spare_part, name='edit_spare_part'),
]
