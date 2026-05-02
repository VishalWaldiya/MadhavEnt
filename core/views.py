from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from inventory.models import StockItem, ScooterModel
from sales.models import SaleRecord
from leads.models import Lead

def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
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
    from django.db.models import Count
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

from django.contrib.auth import get_user_model
from django.contrib import messages
User = get_user_model()

@login_required
def manage_staff(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role', 'SALES')
        if not User.objects.filter(username=username).exists():
            User.objects.create_user(username=username, password=password, role=role)
            messages.success(request, f'Staff {username} added successfully.')
        else:
            messages.error(request, 'Username already exists.')
        return redirect('manage_staff')
    staff = User.objects.all()
    return render(request, 'core/manage_staff.html', {'staff': staff})

def secret_admin_signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if username and password:
            if not User.objects.filter(username=username).exists():
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

from django.db.models import Q

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
        from django.db.models import Q
        from inventory.models import StockItem, ScooterModel
        from sales.models import SaleRecord
        from leads.models import Lead
        from tasks.models import ShopTask, TaskTemplate
        from core.models import Note
        from django.contrib.auth import get_user_model
        from django.urls import reverse
        User = get_user_model()

        q_lower = q.lower()

        # 1. Exact Match & Keyword Redirection Logic
        # A. Keyword Redirections (Admin Only)
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

        # B. Keyword Redirections (All Staff)
        if q_lower in ['leads', 'lead list']:
            return redirect(reverse('leads_list'))
        if q_lower in ['tasks', 'board', 'kanban', 'task board']:
            return redirect(reverse('board_view'))
        if q_lower in ['asset', 'tracking', 'search asset']:
            return redirect(reverse('search_asset'))

        # C. Exact ID / Number Redirections
        # Check for exact Task Number (e.g. REG-1)
        exact_task = ShopTask.objects.filter(task_number__iexact=q).first()
        if exact_task:
            return redirect(reverse('task_detail', args=[exact_task.id]))

        # Check for Invoice ID (e.g. INV-5 or 5)
        invoice_id = None
        if q_lower.startswith('inv-'):
            try: invoice_id = int(q_lower[4:])
            except: pass
        elif q.isdigit():
            invoice_id = int(q)
        
        if invoice_id:
            exact_sale = SaleRecord.objects.filter(id=invoice_id).first()
            if exact_sale:
                return redirect(reverse('invoice_view', args=[exact_sale.id]))

        # Check for exact Serial Number Match
        exact_item = StockItem.objects.filter(serial_number__iexact=q).first()
        if exact_item:
            return redirect(f"{reverse('search_asset')}?q={exact_item.serial_number}")

        # 2. General Search Results
        results['inventory_items'] = StockItem.objects.filter(Q(serial_number__icontains=q) | Q(name__icontains=q))
        results['scooter_models'] = ScooterModel.objects.filter(name__icontains=q)
        
        results['sales'] = SaleRecord.objects.filter(
            Q(customer__first_name__icontains=q) | Q(customer__last_name__icontains=q) | \
            Q(customer__phone_number__icontains=q) | Q(gst_number__icontains=q)
        ).distinct()
        
        results['leads'] = Lead.objects.filter(
            Q(customer__first_name__icontains=q) | Q(customer__last_name__icontains=q) | \
            Q(customer__phone_number__icontains=q)
        ).distinct()

        results['tasks'] = ShopTask.objects.filter(
            Q(task_number__icontains=q) | Q(title__icontains=q) | Q(external_assignee__icontains=q)
        ).distinct()

        # 3. ADMIN-ONLY Search Results
        if request.user.role == 'ADMIN':
            results['customers'] = User.objects.filter(role='CUSTOMER').filter(
                Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(phone_number__icontains=q)
            )
            results['notes'] = Note.objects.filter(Q(title__icontains=q) | Q(content__icontains=q))
            results['templates'] = TaskTemplate.objects.filter(Q(name__icontains=q) | Q(prefix__icontains=q))
            
    return render(request, 'core/global_search_results.html', {'query': q, 'results': results})

@login_required
def manage_customers(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
        
    from django.contrib.auth import get_user_model
    User = get_user_model()
    customers = User.objects.filter(role='CUSTOMER')
    return render(request, 'core/manage_customers.html', {'customers': customers})

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
    from django.shortcuts import get_object_or_404
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
    from django.shortcuts import get_object_or_404
    note = get_object_or_404(Note, id=note_id)
    if request.method == 'POST':
        note.delete()
        messages.success(request, 'Note deleted successfully.')
    return redirect('notes_list')
