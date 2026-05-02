from django.contrib import admin
from django.urls import path, include
from core import views as core_views

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('admin/', admin.site.urls),
    path('', core_views.dashboard, name='dashboard'),
    path('inventory/', include('inventory.urls')),
    path('sales/', include('sales.urls')),
    path('leads/', include('leads.urls')),
    path('tasks/', include('tasks.urls')),
    path('login/', core_views.login_view, name='login'),
    path('logout/', core_views.logout_view, name='logout'),
    path('manage-staff/', core_views.manage_staff, name='manage_staff'),
    path('manage-customers/', core_views.manage_customers, name='manage_customers'),
    path('admin-controls/notes/', core_views.notes_list, name='notes_list'),
    path('admin-controls/notes/add/', core_views.add_note, name='add_note'),
    path('admin-controls/notes/<int:note_id>/edit/', core_views.edit_note, name='edit_note'),
    path('admin-controls/notes/<int:note_id>/delete/', core_views.delete_note, name='delete_note'),
    path('secret-admin-signup-hq/', core_views.secret_admin_signup, name='secret_admin_signup'),
    path('global-search/', core_views.global_search, name='global_search'),
]
