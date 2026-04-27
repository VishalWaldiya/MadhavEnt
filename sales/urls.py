from django.urls import path
from . import views

urlpatterns = [
    path('', views.sales_list, name='sales_list'),
    path('add/', views.add_sale, name='add_sale'),
    path('search/', views.search_asset, name='search_asset'),
    path('gst/', views.gst_report, name='gst_report'),
    path('invoice/<int:sale_id>/', views.invoice_view, name='invoice_view'),
]
