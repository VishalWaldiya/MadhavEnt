from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from .models import ScooterModel, Scooter, Battery, Charger, SparePart

@login_required
def inventory_list(request):
    tab = request.GET.get('tab', 'scooters')
    scooter_models = ScooterModel.objects.all().order_by('name')
    scooters = Scooter.objects.all().order_by('-purchase_date')
    batteries = Battery.objects.all().order_by('-purchase_date')
    chargers = Charger.objects.all().order_by('-purchase_date')
    spare_parts = SparePart.objects.all().order_by('-purchase_date')
    
    return render(request, 'inventory/list.html', {
        'tab': tab,
        'scooter_models': scooter_models,
        'scooters': scooters,
        'batteries': batteries,
        'chargers': chargers,
        'spare_parts': spare_parts,
    })

# ================= ADD VIEWS =================
@login_required
def add_scooter_model(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        watts = request.POST.get('watts') or 1200
        charging_time = request.POST.get('charging_time') or 4.0
        cost_price = request.POST.get('cost_price') or 0.00
        selling_price = request.POST.get('selling_price') or 0.00
        default_range_km = request.POST.get('default_range_km') or 80
        battery_lithium_60w_range = request.POST.get('battery_lithium_60w_range') or 85
        battery_lithium_72w_range = request.POST.get('battery_lithium_72w_range') or 115
        battery_lead_60w_range = request.POST.get('battery_lead_60w_range') or 55
        battery_lead_72w_range = request.POST.get('battery_lead_72w_range') or 70
        description = request.POST.get('description', '')

        ScooterModel.objects.create(
            name=name,
            watts=watts,
            charging_time=charging_time,
            cost_price=cost_price,
            selling_price=selling_price,
            default_range_km=default_range_km,
            battery_lithium_60w_range=battery_lithium_60w_range,
            battery_lithium_72w_range=battery_lithium_72w_range,
            battery_lead_60w_range=battery_lead_60w_range,
            battery_lead_72w_range=battery_lead_72w_range,
            description=description
        )
        messages.success(request, f'Scooter model "{name}" added successfully with configured battery range variants.')
        return redirect(f"{reverse('inventory_list')}?tab=scooters")
    return render(request, 'inventory/add_scooter_model.html')

@login_required
def add_scooter(request):
    if request.method == 'POST':
        model_id = request.POST.get('scooter_model')
        chassis_number = request.POST.get('chassis_number')
        motor_number = request.POST.get('motor_number', '')
        color = request.POST.get('color', 'Standard')
        cost_price = request.POST.get('cost_price') or None
        selling_price = request.POST.get('selling_price') or None
        supplier_details = request.POST.get('supplier_details', '')

        scooter_model = get_object_or_404(ScooterModel, id=model_id)
        
        if not selling_price:
            selling_price = scooter_model.selling_price
        if not cost_price:
            cost_price = scooter_model.cost_price

        Scooter.objects.create(
            scooter_model=scooter_model,
            chassis_number=chassis_number,
            motor_number=motor_number,
            color=color,
            cost_price=cost_price or 0.00,
            selling_price=selling_price or 0.00,
            supplier_details=supplier_details,
            status='AVAILABLE'
        )
        messages.success(request, f'Scooter chassis {chassis_number} ({scooter_model.name}) added to stock.')
        return redirect(f"{reverse('inventory_list')}?tab=scooters")

    models = ScooterModel.objects.all()
    return render(request, 'inventory/add_scooter.html', {'models': models})

@login_required
def add_battery(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        serial_number = request.POST.get('serial_number')
        battery_type = request.POST.get('battery_type', 'LITHIUM')
        voltage = request.POST.get('voltage', '60V')
        capacity_ah = request.POST.get('capacity_ah', '30Ah')
        cost_price = request.POST.get('cost_price') or 0.00
        price_with_scooter = request.POST.get('price_with_scooter') or 0.00
        price_without_scooter = request.POST.get('price_without_scooter') or 0.00
        supplier_details = request.POST.get('supplier_details', '')

        Battery.objects.create(
            name=name,
            serial_number=serial_number,
            battery_type=battery_type,
            voltage=voltage,
            capacity_ah=capacity_ah,
            cost_price=cost_price,
            price_with_scooter=price_with_scooter,
            price_without_scooter=price_without_scooter,
            supplier_details=supplier_details,
            status='AVAILABLE'
        )
        messages.success(request, f'Battery "{name}" ({serial_number}) added to stock.')
        return redirect(f"{reverse('inventory_list')}?tab=batteries")
    return render(request, 'inventory/add_battery.html')

@login_required
def add_charger(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        serial_number = request.POST.get('serial_number')
        charger_type = request.POST.get('charger_type', 'Standard Fast Charger')
        voltage = request.POST.get('voltage', '60V')
        cost_price = request.POST.get('cost_price') or 0.00
        price_with_scooter = request.POST.get('price_with_scooter') or 0.00
        price_without_scooter = request.POST.get('price_without_scooter') or 0.00
        supplier_details = request.POST.get('supplier_details', '')

        Charger.objects.create(
            name=name,
            serial_number=serial_number,
            charger_type=charger_type,
            voltage=voltage,
            cost_price=cost_price,
            price_with_scooter=price_with_scooter,
            price_without_scooter=price_without_scooter,
            supplier_details=supplier_details,
            status='AVAILABLE'
        )
        messages.success(request, f'Charger "{name}" ({serial_number}) added to stock.')
        return redirect(f"{reverse('inventory_list')}?tab=chargers")
    return render(request, 'inventory/add_charger.html')

@login_required
def add_spare_part(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        part_number = request.POST.get('part_number')
        category = request.POST.get('category', 'General Spare')
        quantity = request.POST.get('quantity') or 1
        cost_price = request.POST.get('cost_price') or 0.00
        selling_price = request.POST.get('selling_price') or 0.00
        supplier_details = request.POST.get('supplier_details', '')

        SparePart.objects.create(
            name=name,
            part_number=part_number,
            category=category,
            quantity=int(quantity),
            cost_price=cost_price,
            selling_price=selling_price,
            supplier_details=supplier_details,
            status='AVAILABLE' if int(quantity) > 0 else 'OUT_OF_STOCK'
        )
        messages.success(request, f'Spare Part "{name}" ({part_number}) added to stock.')
        return redirect(f"{reverse('inventory_list')}?tab=spares")
    return render(request, 'inventory/add_spare_part.html')

# ================= EDIT VIEWS (ADMIN PRIVILEGES ONLY) =================
@login_required
def edit_scooter_model(request, model_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Administrator privileges required to edit inventory items.')
        return redirect('inventory_list')
    model = get_object_or_404(ScooterModel, id=model_id)

    if request.method == 'POST':
        model.name = request.POST.get('name')
        model.watts = int(request.POST.get('watts') or 1200)
        model.charging_time = float(request.POST.get('charging_time') or 4.0)
        model.cost_price = request.POST.get('cost_price') or 0.00
        model.selling_price = request.POST.get('selling_price') or 0.00
        model.default_range_km = int(request.POST.get('default_range_km') or 80)
        model.battery_lithium_60w_range = int(request.POST.get('battery_lithium_60w_range') or 85)
        model.battery_lithium_72w_range = int(request.POST.get('battery_lithium_72w_range') or 115)
        model.battery_lead_60w_range = int(request.POST.get('battery_lead_60w_range') or 55)
        model.battery_lead_72w_range = int(request.POST.get('battery_lead_72w_range') or 70)
        model.description = request.POST.get('description', '')
        model.save()
        messages.success(request, f'Scooter model "{model.name}" updated successfully.')
        return redirect(f"{reverse('inventory_list')}?tab=scooters")

    return render(request, 'inventory/edit_scooter_model.html', {'model': model})

@login_required
def edit_scooter(request, item_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Administrator privileges required to edit inventory items.')
        return redirect('inventory_list')
    scooter = get_object_or_404(Scooter, id=item_id)

    if request.method == 'POST':
        model_id = request.POST.get('scooter_model')
        if model_id:
            scooter.scooter_model = get_object_or_404(ScooterModel, id=model_id)
        scooter.chassis_number = request.POST.get('chassis_number')
        scooter.motor_number = request.POST.get('motor_number', '')
        scooter.color = request.POST.get('color', 'Standard')
        scooter.cost_price = request.POST.get('cost_price') or 0.00
        scooter.selling_price = request.POST.get('selling_price') or 0.00
        scooter.status = request.POST.get('status', 'AVAILABLE')
        scooter.supplier_details = request.POST.get('supplier_details', '')
        scooter.save()
        messages.success(request, f'Scooter chassis {scooter.chassis_number} updated successfully.')
        return redirect(f"{reverse('inventory_list')}?tab=scooters")

    models = ScooterModel.objects.all()
    return render(request, 'inventory/edit_scooter.html', {'scooter': scooter, 'models': models})

@login_required
def edit_battery(request, item_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Administrator privileges required to edit inventory items.')
        return redirect('inventory_list')
    battery = get_object_or_404(Battery, id=item_id)

    if request.method == 'POST':
        battery.name = request.POST.get('name')
        battery.serial_number = request.POST.get('serial_number')
        battery.battery_type = request.POST.get('battery_type', 'LITHIUM')
        battery.voltage = request.POST.get('voltage', '60V')
        battery.capacity_ah = request.POST.get('capacity_ah', '30Ah')
        battery.cost_price = request.POST.get('cost_price') or 0.00
        battery.price_with_scooter = request.POST.get('price_with_scooter') or 0.00
        battery.price_without_scooter = request.POST.get('price_without_scooter') or 0.00
        battery.status = request.POST.get('status', 'AVAILABLE')
        battery.supplier_details = request.POST.get('supplier_details', '')
        battery.save()
        messages.success(request, f'Battery "{battery.name}" ({battery.serial_number}) updated successfully.')
        return redirect(f"{reverse('inventory_list')}?tab=batteries")

    return render(request, 'inventory/edit_battery.html', {'battery': battery})

@login_required
def edit_charger(request, item_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Administrator privileges required to edit inventory items.')
        return redirect('inventory_list')
    charger = get_object_or_404(Charger, id=item_id)

    if request.method == 'POST':
        charger.name = request.POST.get('name')
        charger.serial_number = request.POST.get('serial_number')
        charger.charger_type = request.POST.get('charger_type', 'Standard Fast Charger')
        charger.voltage = request.POST.get('voltage', '60V')
        charger.cost_price = request.POST.get('cost_price') or 0.00
        charger.price_with_scooter = request.POST.get('price_with_scooter') or 0.00
        charger.price_without_scooter = request.POST.get('price_without_scooter') or 0.00
        charger.status = request.POST.get('status', 'AVAILABLE')
        charger.supplier_details = request.POST.get('supplier_details', '')
        charger.save()
        messages.success(request, f'Charger "{charger.name}" ({charger.serial_number}) updated successfully.')
        return redirect(f"{reverse('inventory_list')}?tab=chargers")

    return render(request, 'inventory/edit_charger.html', {'charger': charger})

@login_required
def edit_spare_part(request, item_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Administrator privileges required to edit inventory items.')
        return redirect('inventory_list')
    spare = get_object_or_404(SparePart, id=item_id)

    if request.method == 'POST':
        spare.name = request.POST.get('name')
        spare.part_number = request.POST.get('part_number')
        spare.category = request.POST.get('category', 'General Spare')
        qty = int(request.POST.get('quantity') or 0)
        spare.quantity = qty
        spare.cost_price = request.POST.get('cost_price') or 0.00
        spare.selling_price = request.POST.get('selling_price') or 0.00
        spare.status = 'AVAILABLE' if qty > 0 else 'OUT_OF_STOCK'
        spare.supplier_details = request.POST.get('supplier_details', '')
        spare.save()
        messages.success(request, f'Spare Part "{spare.name}" ({spare.part_number}) updated successfully.')
        return redirect(f"{reverse('inventory_list')}?tab=spares")

    return render(request, 'inventory/edit_spare_part.html', {'spare': spare})

# ================= DELETE VIEWS (ADMIN PRIVILEGES ONLY) =================
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
            'cancel_url': reverse('inventory_list'),
        })
    if request.method == 'POST':
        scooter.delete(cascade=True)
        messages.success(request, f'Scooter model {scooter.name} moved to Recycle Bin.')
    return redirect('inventory_list')

@login_required
def delete_scooter(request, item_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('inventory_list')
    item = get_object_or_404(Scooter, id=item_id)
    if request.method == 'POST':
        item.delete(cascade=True)
        messages.success(request, f'Scooter chassis {item.chassis_number} moved to Recycle Bin.')
    return redirect(f"{reverse('inventory_list')}?tab=scooters")

@login_required
def delete_battery(request, item_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('inventory_list')
    item = get_object_or_404(Battery, id=item_id)
    if request.method == 'POST':
        item.delete(cascade=True)
        messages.success(request, f'Battery {item.serial_number} moved to Recycle Bin.')
    return redirect(f"{reverse('inventory_list')}?tab=batteries")

@login_required
def delete_charger(request, item_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('inventory_list')
    item = get_object_or_404(Charger, id=item_id)
    if request.method == 'POST':
        item.delete(cascade=True)
        messages.success(request, f'Charger {item.serial_number} moved to Recycle Bin.')
    return redirect(f"{reverse('inventory_list')}?tab=chargers")

@login_required
def delete_spare_part(request, item_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('inventory_list')
    item = get_object_or_404(SparePart, id=item_id)
    if request.method == 'POST':
        item.delete(cascade=True)
        messages.success(request, f'Spare Part {item.name} moved to Recycle Bin.')
    return redirect(f"{reverse('inventory_list')}?tab=spares")
