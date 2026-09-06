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
    path('manage-staff/<int:user_id>/delete/', core_views.delete_staff, name='delete_staff'),
    path('manage-customers/', core_views.manage_customers, name='manage_customers'),
    path('manage-customers/<int:customer_id>/delete/', core_views.delete_customer, name='delete_customer'),
    path('admin-controls/notes/', core_views.notes_list, name='notes_list'),
    path('admin-controls/notes/add/', core_views.add_note, name='add_note'),
    path('admin-controls/notes/<int:note_id>/edit/', core_views.edit_note, name='edit_note'),
    path('admin-controls/notes/<int:note_id>/delete/', core_views.delete_note, name='delete_note'),
    path('admin-controls/recycle-bin/', core_views.recycle_bin, name='recycle_bin'),
    path('admin-controls/recycle-bin/restore/<str:model_name>/<int:item_id>/', core_views.restore_item, name='restore_item'),
    path('admin-controls/recycle-bin/delete-permanent/<str:model_name>/<int:item_id>/', core_views.hard_delete_item, name='hard_delete_item'),
    path('admin-controls/recycle-bin/empty/', core_views.empty_recycle_bin, name='empty_recycle_bin'),
    path('secret-admin-signup-hq/', core_views.secret_admin_signup, name='secret_admin_signup'),
    path('global-search/', core_views.global_search, name='global_search'),
    path('manifest.json', core_views.manifest_view, name='manifest'),
    path('sw.js', core_views.serviceworker_view, name='service_worker'),
    path('offline/', core_views.offline_view, name='offline'),
    path('notifications/subscribe/', core_views.subscribe_push_device, name='subscribe_push_device'),
    path('notifications/preferences/', core_views.update_notification_preferences, name='update_notification_preferences'),
    path('notifications/get/', core_views.get_user_notifications, name='get_user_notifications'),
    path('admin-controls/broadcast-notification/', core_views.broadcast_notification_view, name='broadcast_notification'),
]

