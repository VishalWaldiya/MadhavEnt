from django.urls import path
from . import views

urlpatterns = [
    path('', views.leads_list, name='leads_list'),
    path('add/', views.add_lead, name='add_lead'),
    path('<int:lead_id>/', views.lead_detail, name='lead_detail'),
    path('<int:lead_id>/edit/', views.edit_lead, name='edit_lead'),
    path('<int:lead_id>/add-note/', views.add_lead_note, name='add_lead_note'),
    path('<int:lead_id>/update-status/', views.update_lead_status, name='update_lead_status'),
    path('<int:lead_id>/quote/', views.add_quote, name='add_quote'),
    path('<int:lead_id>/reject/', views.reject_lead, name='reject_lead'),
    path('<int:lead_id>/delete/', views.delete_lead, name='delete_lead'),
]
