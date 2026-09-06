from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Lead, Quote, LeadRequirement
from inventory.models import ScooterModel, StockItem
from django.contrib import messages
from django.urls import reverse
import uuid

@login_required
def leads_list(request):
    leads = Lead.objects.all().order_by('-created_at')
    return render(request, 'leads/list.html', {'leads': leads})

@login_required
def add_lead(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone_number = request.POST.get('phone_number', '')
        interested_items_text = request.POST.get('interested_items', '')
        
        aadhar_number = request.POST.get('aadhar_number')
        pan_number = request.POST.get('pan_number')
        aadhar_front_photo = request.FILES.get('aadhar_front_photo')
        aadhar_back_photo = request.FILES.get('aadhar_back_photo')
        pan_photo = request.FILES.get('pan_photo')
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        customer, created = User.all_objects.get_or_create(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            defaults={
                'role': 'CUSTOMER',
                'username': f"cust_{phone_number}_{uuid.uuid4().hex[:6]}",
            }
        )
        
        if aadhar_number: customer.aadhar_number = aadhar_number
        if pan_number: customer.pan_number = pan_number
        if aadhar_front_photo: customer.aadhar_front_photo = aadhar_front_photo
        if aadhar_back_photo: customer.aadhar_back_photo = aadhar_back_photo
        if pan_photo: customer.pan_photo = pan_photo
        customer.save()
        
        lead = Lead.objects.create(
            customer=customer,
            interested_items=interested_items_text,
            salesperson=request.user
        )

        # Process Requirement Line Items
        sources = request.POST.getlist('req_source_type')
        scooter_ids = request.POST.getlist('req_scooter_id')
        stock_ids = request.POST.getlist('req_stock_id')
        custom_names = request.POST.getlist('req_custom_name')
        unit_prices = request.POST.getlist('req_unit_price')
        quantities = request.POST.getlist('req_quantity')
        add_to_inv_flags = request.POST.getlist('req_add_to_inv')

        requirement_names = []

        for i in range(len(sources)):
            stype = sources[i] if i < len(sources) else 'CUSTOM'
            try:
                u_price = float(unit_prices[i]) if i < len(unit_prices) and unit_prices[i] else 0.0
            except ValueError:
                u_price = 0.0

            try:
                qty = int(quantities[i]) if i < len(quantities) and quantities[i] else 1
            except ValueError:
                qty = 1

            add_to_inv = add_to_inv_flags[i] if i < len(add_to_inv_flags) else '0'

            scooter_obj = None
            stock_obj = None
            custom_name = ''

            if stype == 'SCOOTER':
                s_id = scooter_ids[i] if i < len(scooter_ids) else None
                if s_id:
                    scooter_obj = ScooterModel.objects.filter(id=s_id).first()
            elif stype == 'STOCK':
                st_id = stock_ids[i] if i < len(stock_ids) else None
                if st_id:
                    stock_obj = StockItem.objects.filter(id=st_id).first()
            elif stype == 'CUSTOM':
                custom_name = custom_names[i] if i < len(custom_names) else 'Custom Item'
                if add_to_inv == '1' and custom_name:
                    stock_obj = StockItem.objects.create(
                        name=custom_name,
                        item_type='SPARE',
                        serial_number=f"SPARE-{uuid.uuid4().hex[:8].upper()}",
                        status='AVAILABLE'
                    )

            if scooter_obj or stock_obj or custom_name:
                req = LeadRequirement.objects.create(
                    lead=lead,
                    scooter_model=scooter_obj,
                    stock_item=stock_obj,
                    custom_item_name=custom_name if not stock_obj else '',
                    unit_price=u_price,
                    quantity=qty,
                )
                requirement_names.append(req.get_item_name())

        if requirement_names:
            summary = ", ".join(requirement_names)
            if interested_items_text:
                lead.interested_items = f"{interested_items_text} | Requirements: {summary}"
            else:
                lead.interested_items = summary
            lead.save()

        messages.success(request, 'Lead captured with requirement details successfully.')
        return redirect('leads_list')

    scooters = ScooterModel.objects.all()
    stock_items = StockItem.objects.all()
    return render(request, 'leads/add_lead.html', {
        'scooters': scooters,
        'stock_items': stock_items
    })

@login_required
def add_quote(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    if request.method == 'POST':
        scooter_model_id = request.POST.get('scooter_model')
        quoted_price = request.POST.get('quoted_price')
        item_details = request.POST.get('item_details')
        valid_until = request.POST.get('valid_until')

        battery_id = request.POST.get('battery')
        charger_id = request.POST.get('charger')
        
        scooter_model = ScooterModel.objects.filter(id=scooter_model_id).first() if scooter_model_id else None
        battery = StockItem.objects.filter(id=battery_id).first() if battery_id else None
        charger = StockItem.objects.filter(id=charger_id).first() if charger_id else None
            
        Quote.objects.create(
            lead=lead,
            scooter_model=scooter_model,
            battery=battery,
            charger=charger,
            quoted_price=quoted_price,
            item_details=item_details,
            valid_until=valid_until
        )
        messages.success(request, 'Quote generated successfully.')
        return redirect('leads_list')

    scooters = ScooterModel.objects.all()
    batteries = StockItem.objects.filter(item_type='BATTERY', status='AVAILABLE')
    chargers = StockItem.objects.filter(item_type='CHARGER', status='AVAILABLE')
    return render(request, 'leads/add_quote.html', {'lead': lead, 'scooters': scooters, 'batteries': batteries, 'chargers': chargers})

@login_required
def reject_lead(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    if request.method == 'POST':
        reason = request.POST.get('rejection_reason', '')
        lead.status = 'REJECTED'
        lead.rejection_reason = reason
        lead.save()
        messages.success(request, f'Lead for {lead.customer.get_full_name()} has been rejected.')
    return redirect('leads_list')

@login_required
def delete_lead(request, lead_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Only administrators can delete leads.')
        return redirect('leads_list')
    lead = get_object_or_404(Lead, id=lead_id)
    connected = lead.get_connected_resources(include_deleted=False)

    if connected and request.POST.get('confirmed') != '1':
        return render(request, 'core/delete_confirm.html', {
            'item_type': 'Lead',
            'item_title': f"Lead for {lead.customer.get_full_name() if lead.customer else 'Unknown'}",
            'connected_items': connected,
            'action_url': reverse('delete_lead', args=[lead.id]),
            'cancel_url': request.META.get('HTTP_REFERER') or reverse('leads_list'),
        })

    if request.method == 'POST':
        cust_name = lead.customer.get_full_name() if lead.customer else 'Unknown'
        lead.delete(cascade=True)
        msg = f'Lead for {cust_name} moved to Recycle Bin.'
        if connected:
            msg += f' ({len(connected)} connected resource(s) also soft-deleted).'
        messages.success(request, msg)
    return redirect('leads_list')
