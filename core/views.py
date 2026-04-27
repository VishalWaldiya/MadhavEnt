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
    
    return render(request, 'core/dashboard.html', {
        'scooters': scooters,
        'recent_sales': recent_sales,
        'new_leads': new_leads,
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
        'leads': []
    }
    
    if q:
        # Search Inventory Items
        results['inventory_items'] = StockItem.objects.filter(
            Q(serial_number__icontains=q) | Q(name__icontains=q)
        )
        
        # Search Scooter Models
        results['scooter_models'] = ScooterModel.objects.filter(
            name__icontains=q
        )
        
        # Search Sales / Invoices
        sales_query = Q(customer_name__icontains=q) | \
                      Q(customer_contact__icontains=q) | \
                      Q(aadhar_number__icontains=q) | \
                      Q(pan_number__icontains=q) | \
                      Q(gst_number__icontains=q)
        if q.isdigit():
            sales_query |= Q(id=int(q))
            
        results['sales'] = SaleRecord.objects.filter(sales_query).distinct()
        
        # Search Leads
        results['leads'] = Lead.objects.filter(
            Q(customer_name__icontains=q) | 
            Q(contact__icontains=q) |
            Q(aadhar_number__icontains=q) |
            Q(pan_number__icontains=q)
        ).distinct()
        
    return render(request, 'core/global_search_results.html', {'query': q, 'results': results})
