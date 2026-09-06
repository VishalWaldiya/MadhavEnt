from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db.models import Q, Count, ProtectedError
from django.urls import reverse
from django.http import HttpResponse, FileResponse, JsonResponse
from django.conf import settings
import os
import json

from inventory.models import StockItem, ScooterModel
from sales.models import SaleRecord
from leads.models import Lead
from core.models import NotificationPreference, PushDeviceSubscription, BroadcastNotificationLog, Note



User = get_user_model()

def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            if getattr(user, 'is_deleted', False):
                return render(request, 'core/login.html', {'error': 'Account has been soft-deleted. Contact Administrator.'})
            login(request, user)
            return redirect('dashboard')
        return render(request, 'core/login.html', {'error': 'Invalid credentials'})
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    scooters = ScooterModel.objects.all()
    recent_sales = SaleRecord.objects.order_by('-sale_date')[:5]
    new_leads = Lead.objects.filter(status='NEW')
    
    # Low stock alerts
    low_stock_alerts = []
    # Check Scooters
    for s in scooters:
        count = StockItem.objects.filter(scooter_model=s, status='AVAILABLE').count()
        if count < 2:
            low_stock_alerts.append({
                'item': s.name,
                'count': count,
                'type': 'Scooter'
            })
    
    # Check other items (Batteries, Chargers, Parts)
    other_items = StockItem.objects.filter(scooter_model__isnull=True, status='AVAILABLE')\
        .values('item_type', 'name')\
        .annotate(total=Count('id'))
    
    for item in other_items:
        if item['total'] < 2:
            low_stock_alerts.append({
                'item': item['name'] or item['item_type'],
                'count': item['total'],
                'type': item['item_type'].title()
            })
    
    return render(request, 'core/dashboard.html', {
        'scooters': scooters,
        'recent_sales': recent_sales,
        'new_leads': new_leads,
        'low_stock_alerts': low_stock_alerts,
    })

@login_required
def manage_staff(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role', 'SALES')
        if not User.all_objects.filter(username=username).exists():
            User.objects.create_user(username=username, password=password, role=role)
            messages.success(request, f'Staff {username} added successfully.')
        else:
            messages.error(request, 'Username already exists.')
        return redirect('manage_staff')
    staff = User.objects.exclude(role='CUSTOMER')
    return render(request, 'core/manage_staff.html', {'staff': staff})

@login_required
def delete_staff(request, user_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Only administrators can perform this action.')
        return redirect('dashboard')
    if request.user.id == user_id:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('manage_staff')
    user = get_object_or_404(User.all_objects, id=user_id)
    connected = user.get_connected_resources(include_deleted=False)

    if connected and request.POST.get('confirmed') != '1':
        return render(request, 'core/delete_confirm.html', {
            'item_type': 'Staff User',
            'item_title': user.username,
            'connected_items': connected,
            'action_url': reverse('delete_staff', args=[user.id]),
            'cancel_url': request.META.get('HTTP_REFERER') or reverse('manage_staff'),
        })

    if request.method == 'POST':
        user.delete(cascade=True)
        msg = f'Staff member {user.username} moved to Recycle Bin.'
        if connected:
            msg += f' ({len(connected)} connected resource(s) also soft-deleted).'
        messages.success(request, msg)
    return redirect('manage_staff')

@login_required
def manage_customers(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    customers = User.objects.filter(role='CUSTOMER')
    return render(request, 'core/manage_customers.html', {'customers': customers})

@login_required
def delete_customer(request, customer_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Only administrators can perform this action.')
        return redirect('dashboard')
    customer = get_object_or_404(User.all_objects, id=customer_id)
    connected = customer.get_connected_resources(include_deleted=False)

    if connected and request.POST.get('confirmed') != '1':
        return render(request, 'core/delete_confirm.html', {
            'item_type': 'Customer Profile',
            'item_title': customer.get_full_name() or customer.username,
            'connected_items': connected,
            'action_url': reverse('delete_customer', args=[customer.id]),
            'cancel_url': request.META.get('HTTP_REFERER') or reverse('manage_customers'),
        })

    if request.method == 'POST':
        customer.delete(cascade=True)
        msg = f'Customer {customer.get_full_name() or customer.username} moved to Recycle Bin.'
        if connected:
            msg += f' ({len(connected)} connected resource(s) also soft-deleted).'
        messages.success(request, msg)
    return redirect('manage_customers')

def secret_admin_signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if username and password:
            if not User.all_objects.filter(username=username).exists():
                user = User.objects.create_user(username=username, password=password, role='ADMIN')
                user.is_staff = True
                user.is_superuser = True
                user.save()
                messages.success(request, f'Admin user {username} created successfully. You can now login.')
                return redirect('login')
            else:
                messages.error(request, 'Username already exists.')
        else:
            messages.error(request, 'Please provide both username and password.')
    return render(request, 'core/secret_admin_signup.html')

@login_required
def global_search(request):
    q = request.GET.get('q', '').strip()
    results = {
        'inventory_items': [],
        'scooter_models': [],
        'sales': [],
        'leads': [],
        'customers': [],
        'tasks': [],
        'notes': [],
        'templates': []
    }
    
    if q:
        from tasks.models import ShopTask, TaskTemplate
        from core.models import Note

        q_lower = q.lower()

        # 1. Exact Match & Keyword Redirection Logic (only redirect if target is active)
        if request.user.role == 'ADMIN':
            if q_lower in ['gst', 'report', 'gst report']:
                return redirect(reverse('gst_report'))
            if q_lower in ['staff', 'manage staff']:
                return redirect(reverse('manage_staff'))
            if q_lower in ['customers', 'crm', 'manage customers']:
                return redirect(reverse('manage_customers'))
            if q_lower in ['notes', 'notepad', 'shop notepad']:
                return redirect(reverse('notes_list'))
            if q_lower in ['inventory', 'stock']:
                return redirect(reverse('inventory_list'))
            if q_lower in ['sales module', 'sales list']:
                return redirect(reverse('sales_list'))

        if q_lower in ['leads', 'lead list']:
            return redirect(reverse('leads_list'))
        if q_lower in ['tasks', 'board', 'kanban', 'task board']:
            return redirect(reverse('board_view'))
        if q_lower in ['asset', 'tracking', 'search asset']:
            return redirect(reverse('search_asset'))

        # Check for exact Task Number
        exact_task = ShopTask.all_objects.filter(task_number__iexact=q).first()
        if exact_task and not exact_task.is_deleted:
            return redirect(reverse('task_detail', args=[exact_task.id]))

        # Check for Invoice ID
        invoice_id = None
        if q_lower.startswith('inv-'):
            try: invoice_id = int(q_lower[4:])
            except: pass
        elif q.isdigit():
            invoice_id = int(q)
        
        if invoice_id:
            exact_sale = SaleRecord.all_objects.filter(id=invoice_id).first()
            if exact_sale and not exact_sale.is_deleted:
                return redirect(reverse('invoice_view', args=[exact_sale.id]))

        # Check for exact Serial Number Match
        exact_item = StockItem.all_objects.filter(serial_number__iexact=q).first()
        if exact_item and not exact_item.is_deleted:
            return redirect(f"{reverse('search_asset')}?q={exact_item.serial_number}")

        # 2. General Search Results (Includes soft deleted items using all_objects)
        results['inventory_items'] = StockItem.all_objects.filter(Q(serial_number__icontains=q) | Q(name__icontains=q))
        results['scooter_models'] = ScooterModel.all_objects.filter(name__icontains=q)
        
        results['sales'] = SaleRecord.all_objects.filter(
            Q(customer__first_name__icontains=q) | Q(customer__last_name__icontains=q) | \
            Q(customer__phone_number__icontains=q) | Q(gst_number__icontains=q)
        ).distinct()
        
        results['leads'] = Lead.all_objects.filter(
            Q(customer__first_name__icontains=q) | Q(customer__last_name__icontains=q) | \
            Q(customer__phone_number__icontains=q)
        ).distinct()

        results['tasks'] = ShopTask.all_objects.filter(
            Q(task_number__icontains=q) | Q(title__icontains=q) | Q(external_assignee__icontains=q)
        ).distinct()

        # 3. ADMIN-ONLY Search Results
        if request.user.role == 'ADMIN':
            results['customers'] = User.all_objects.filter(role='CUSTOMER').filter(
                Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(phone_number__icontains=q) | Q(username__icontains=q)
            )
            results['notes'] = Note.all_objects.filter(Q(title__icontains=q) | Q(content__icontains=q))
            results['templates'] = TaskTemplate.all_objects.filter(Q(name__icontains=q) | Q(prefix__icontains=q))
            
    return render(request, 'core/global_search_results.html', {'query': q, 'results': results})

@login_required
def notes_list(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    from .models import Note
    notes = Note.objects.all().order_by('-updated_at')
    return render(request, 'core/notes_list.html', {'notes': notes})

@login_required
def add_note(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    from .models import Note
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        Note.objects.create(title=title, content=content)
        messages.success(request, 'Note created successfully.')
        return redirect('notes_list')
    return render(request, 'core/note_form.html')

@login_required
def edit_note(request, note_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    from .models import Note
    note = get_object_or_404(Note, id=note_id)
    if request.method == 'POST':
        note.title = request.POST.get('title')
        note.content = request.POST.get('content')
        note.save()
        messages.success(request, 'Note updated successfully.')
        return redirect('notes_list')
    return render(request, 'core/note_form.html', {'note': note})

@login_required
def delete_note(request, note_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    from .models import Note
    note = get_object_or_404(Note, id=note_id)
    if request.method == 'POST':
        note.delete() # Soft delete
        messages.success(request, 'Note moved to Recycle Bin.')
    return redirect('notes_list')

@login_required
def recycle_bin(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    from tasks.models import ShopTask, TaskTemplate
    from core.models import Note

    deleted_staff = User.all_objects.filter(is_deleted=True).exclude(role='CUSTOMER')
    deleted_customers = User.all_objects.filter(is_deleted=True, role='CUSTOMER')
    deleted_stock_items = StockItem.all_objects.filter(is_deleted=True)
    deleted_scooter_models = ScooterModel.all_objects.filter(is_deleted=True)
    deleted_sales = SaleRecord.all_objects.filter(is_deleted=True)
    deleted_leads = Lead.all_objects.filter(is_deleted=True)
    deleted_tasks = ShopTask.all_objects.filter(is_deleted=True)
    deleted_notes = Note.all_objects.filter(is_deleted=True)
    deleted_templates = TaskTemplate.all_objects.filter(is_deleted=True)

    total_deleted = (
        deleted_staff.count() + deleted_customers.count() +
        deleted_stock_items.count() + deleted_scooter_models.count() +
        deleted_sales.count() + deleted_leads.count() +
        deleted_tasks.count() + deleted_notes.count() + deleted_templates.count()
    )

    return render(request, 'core/recycle_bin.html', {
        'deleted_staff': deleted_staff,
        'deleted_customers': deleted_customers,
        'deleted_stock_items': deleted_stock_items,
        'deleted_scooter_models': deleted_scooter_models,
        'deleted_sales': deleted_sales,
        'deleted_leads': deleted_leads,
        'deleted_tasks': deleted_tasks,
        'deleted_notes': deleted_notes,
        'deleted_templates': deleted_templates,
        'total_deleted': total_deleted,
    })

@login_required
def restore_item(request, model_name, item_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    from tasks.models import ShopTask, TaskTemplate
    from core.models import Note

    model_map = {
        'user': User,
        'note': Note,
        'stockitem': StockItem,
        'scootermodel': ScooterModel,
        'salerecord': SaleRecord,
        'lead': Lead,
        'shoptask': ShopTask,
        'tasktemplate': TaskTemplate,
    }
    model = model_map.get(model_name.lower())
    if not model:
        messages.error(request, 'Invalid model specified.')
        return redirect('recycle_bin')
    
    item = get_object_or_404(model.all_objects, id=item_id)
    item.restore()
    messages.success(request, f'{model._meta.verbose_name.title()} restored successfully.')
    return redirect('recycle_bin')

from django.db.models import ProtectedError

@login_required
def hard_delete_item(request, model_name, item_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    from tasks.models import ShopTask, TaskTemplate
    from core.models import Note

    model_map = {
        'user': User,
        'note': Note,
        'stockitem': StockItem,
        'scootermodel': ScooterModel,
        'salerecord': SaleRecord,
        'lead': Lead,
        'shoptask': ShopTask,
        'tasktemplate': TaskTemplate,
    }
    model = model_map.get(model_name.lower())
    if not model:
        messages.error(request, 'Invalid model specified.')
        return redirect('recycle_bin')
    
    item = get_object_or_404(model.all_objects, id=item_id)
    if request.method == 'POST':
        try:
            item.delete(hard=True)
            messages.success(request, f'{model._meta.verbose_name.title()} permanently deleted.')
        except ProtectedError:
            messages.error(request, f'Cannot permanently delete {model._meta.verbose_name.title()}: it is referenced by active records in the system.')
    return redirect('recycle_bin')

@login_required
def empty_recycle_bin(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        from tasks.models import ShopTask, TaskTemplate
        from leads.models import Lead, Quote
        from core.models import Note

        models_list = [Quote, Lead, SaleRecord, ShopTask, TaskTemplate, StockItem, ScooterModel, Note, User]
        
        deleted_count = 0
        protected_count = 0

        for model in models_list:
            for item in list(model.all_objects.filter(is_deleted=True)):
                try:
                    item.delete(hard=True)
                    deleted_count += 1
                except ProtectedError:
                    protected_count += 1
        
        if protected_count > 0:
            messages.warning(request, f'Emptied {deleted_count} item(s). {protected_count} item(s) could not be deleted because they are referenced by active records.')
        else:
            messages.success(request, f'Recycle bin emptied successfully ({deleted_count} item(s) permanently deleted).')
            
    return redirect('recycle_bin')


def manifest_view(request):
    manifest_path = os.path.join(settings.BASE_DIR, 'static', 'manifest.json')
    if os.path.exists(manifest_path):
        with open(manifest_path, 'rb') as f:
            return HttpResponse(f.read(), content_type='application/manifest+json')
    return HttpResponse(status=404)


def serviceworker_view(request):
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'sw.js')
    if os.path.exists(sw_path):
        with open(sw_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/javascript')
            response['Service-Worker-Allowed'] = '/'
            return response
    return HttpResponse(status=404)



def offline_view(request):
    return render(request, 'offline.html')


def dispatch_push_notification(category, title, message, target_url='/', sender=None):
    log = BroadcastNotificationLog.objects.create(
        category=category,
        title=title,
        message=message,
        target_url=target_url,
        sender=sender
    )
    
    pref_field_map = {
        'SALE': 'notify_on_sale',
        'TASK_COMMENT': 'notify_on_task_comment',
        'BROADCAST': 'notify_on_broadcast',
    }
    
    field = pref_field_map.get(category, 'notify_on_broadcast')
    users = User.objects.filter(is_active=True, is_deleted=False)
    users = users.filter(
        Q(notification_preference__isnull=True) | Q(**{f'notification_preference__{field}': True})
    )
    
    if sender:
        users = users.exclude(id=sender.id)
        
    subscriptions = PushDeviceSubscription.objects.filter(user__in=users)
    return {
        'log_id': log.id,
        'targeted_users': list(users.values_list('id', flat=True)),
        'subscriptions_count': subscriptions.count()
    }


@login_required
def subscribe_push_device(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            endpoint = data.get('endpoint')
            p256dh = data.get('p256dh', '')
            auth = data.get('auth', '')
            browser_info = data.get('browser_info', request.META.get('HTTP_USER_AGENT', 'Browser'))
            
            if endpoint:
                sub, created = PushDeviceSubscription.objects.update_or_create(
                    endpoint=endpoint,
                    defaults={
                        'user': request.user,
                        'p256dh': p256dh,
                        'auth': auth,
                        'browser_info': str(browser_info)[:250]
                    }
                )
                return JsonResponse({'status': 'success', 'created': created})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'invalid method'}, status=405)


@login_required
def update_notification_preferences(request):
    pref, created = NotificationPreference.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        pref.notify_on_sale = request.POST.get('notify_on_sale') in ['on', 'true', True]
        pref.notify_on_task_comment = request.POST.get('notify_on_task_comment') in ['on', 'true', True]
        pref.notify_on_broadcast = request.POST.get('notify_on_broadcast') in ['on', 'true', True]
        pref.save()
        messages.success(request, 'Notification preferences updated.')
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        return redirect(request.META.get('HTTP_REFERER') or 'dashboard')
    
    return JsonResponse({
        'notify_on_sale': pref.notify_on_sale,
        'notify_on_task_comment': pref.notify_on_task_comment,
        'notify_on_broadcast': pref.notify_on_broadcast,
    })


@login_required
def get_user_notifications(request):
    pref, _ = NotificationPreference.objects.get_or_create(user=request.user)
    categories = []
    if pref.notify_on_sale: categories.append('SALE')
    if pref.notify_on_task_comment: categories.append('TASK_COMMENT')
    if pref.notify_on_broadcast: categories.append('BROADCAST')
    
    logs = BroadcastNotificationLog.objects.filter(category__in=categories)[:20]
    data = [{
        'id': log.id,
        'title': log.title,
        'message': log.message,
        'category': log.category,
        'target_url': log.target_url,
        'sent_at': log.sent_at.strftime('%Y-%m-%d %H:%M')
    } for log in logs]
    return JsonResponse({'notifications': data})


@login_required
def broadcast_notification_view(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()
        target_url = request.POST.get('target_url', '/').strip() or '/'
        
        if title and message:
            result = dispatch_push_notification(
                category='BROADCAST',
                title=title,
                message=message,
                target_url=target_url,
                sender=request.user
            )
            messages.success(request, f'📢 Broadcast notification dispatched to {result["subscriptions_count"]} registered device(s).')
            return redirect('broadcast_notification')
        else:
            messages.error(request, 'Please provide both title and message.')
            
    recent_broadcasts = BroadcastNotificationLog.objects.filter(category='BROADCAST')[:10]
    return render(request, 'core/broadcast_notification.html', {'recent_broadcasts': recent_broadcasts})

