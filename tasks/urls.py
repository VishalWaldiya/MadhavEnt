from django.urls import path
from . import views

urlpatterns = [
    path('board/', views.board_view, name='board_view'),
    path('templates/', views.template_list, name='template_list'),
    path('templates/add/', views.add_template, name='add_template'),
    path('add/', views.add_task, name='add_task'),
    path('update/<int:task_id>/', views.update_task_stage, name='update_task_stage'),
    path('<int:task_id>/', views.task_detail, name='task_detail'),
    path('<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('<int:task_id>/add-photo/', views.add_task_photo, name='add_task_photo'),
]
