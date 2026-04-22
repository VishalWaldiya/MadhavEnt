from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ScooterModel, StockItem
from django.contrib import messages

@login_required
def inventory_list(request):
    items = StockItem.objects.all().order_by('-purchase_date')
    scooters = ScooterModel.objects.all()
    return render(request, 'inventory/list.html', {
        'items': items,
        'scooters': scooters
    })

@login_required
def add_scooter_model(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        range_km = request.POST.get('range_km')
        watts = request.POST.get('watts')
        charging_time = request.POST.get('charging_time')
        last_price = request.POST.get('last_price')
        ScooterModel.objects.create(
            name=name, range_km=range_km, watts=watts, 
            charging_time=charging_time, last_price=last_price
        )
        messages.success(request, 'Scooter model added successfully.')
        return redirect('inventory_list')
    return render(request, 'inventory/add_scooter_model.html')

@login_required
def add_stock_item(request):
    if request.method == 'POST':
        item_type = request.POST.get('item_type')
        serial_number = request.POST.get('serial_number')
        name = request.POST.get('name')
        supplier_details = request.POST.get('supplier_details')
        model_id = request.POST.get('scooter_model')
        
        scooter_model = None
        if model_id:
            scooter_model = ScooterModel.objects.get(id=model_id)

        StockItem.objects.create(
            item_type=item_type,
            serial_number=serial_number,
            name=name,
            supplier_details=supplier_details,
            scooter_model=scooter_model
        )
        messages.success(request, 'Stock item added successfully.')
        return redirect('inventory_list')
    
    scooters = ScooterModel.objects.all()
    return render(request, 'inventory/add_stock_item.html', {'scooters': scooters})
