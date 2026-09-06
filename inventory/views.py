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

from django.urls import reverse

@login_required
def delete_stock_item(request, item_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Only administrators can delete stock items.')
        return redirect('inventory_list')
    item = get_object_or_404(StockItem, id=item_id)
    connected = item.get_connected_resources(include_deleted=False)

    if connected and request.POST.get('confirmed') != '1':
        return render(request, 'core/delete_confirm.html', {
            'item_type': 'Stock Item',
            'item_title': f"{item.get_item_type_display()} - {item.serial_number}",
            'connected_items': connected,
            'action_url': reverse('delete_stock_item', args=[item.id]),
            'cancel_url': request.META.get('HTTP_REFERER') or reverse('inventory_list'),
        })

    if request.method == 'POST':
        item.delete(cascade=True)
        msg = f'Stock item {item.serial_number} moved to Recycle Bin.'
        if connected:
            msg += f' ({len(connected)} connected resource(s) also soft-deleted).'
        messages.success(request, msg)
    return redirect('inventory_list')

@login_required
def delete_scooter_model(request, model_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Only administrators can delete scooter models.')
        return redirect('inventory_list')
    scooter = get_object_or_404(ScooterModel, id=model_id)
    connected = scooter.get_connected_resources(include_deleted=False)

    if connected and request.POST.get('confirmed') != '1':
        return render(request, 'core/delete_confirm.html', {
            'item_type': 'Scooter Model',
            'item_title': scooter.name,
            'connected_items': connected,
            'action_url': reverse('delete_scooter_model', args=[scooter.id]),
            'cancel_url': request.META.get('HTTP_REFERER') or reverse('inventory_list'),
        })

    if request.method == 'POST':
        scooter.delete(cascade=True)
        msg = f'Scooter model {scooter.name} moved to Recycle Bin.'
        if connected:
            msg += f' ({len(connected)} connected resource(s) also soft-deleted).'
        messages.success(request, msg)
    return redirect('inventory_list')
