from django.urls import path
from . import views

urlpatterns = [
    path('', views.leads_list, name='leads_list'),
    path('add/', views.add_lead, name='add_lead'),
    path('<int:lead_id>/quote/', views.add_quote, name='add_quote'),
    path('<int:lead_id>/reject/', views.reject_lead, name='reject_lead'),
]
