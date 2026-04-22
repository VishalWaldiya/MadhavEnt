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
