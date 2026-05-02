from django.urls import path
from . import views

urlpatterns = [
    path('board/', views.board_view, name='board_view'),
    path('templates/', views.template_list, name='template_list'),
    path('templates/add/', views.add_template, name='add_template'),
    path('add/', views.add_task, name='add_task'),
    path('update/<int:task_id>/', views.update_task_stage, name='update_task_stage'),
]
