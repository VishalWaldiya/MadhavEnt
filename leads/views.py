from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Lead, Quote
from inventory.models import ScooterModel, StockItem
from django.contrib import messages

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
        interested_items = request.POST.get('interested_items', '')
        
        aadhar_number = request.POST.get('aadhar_number')
        pan_number = request.POST.get('pan_number')
        aadhar_front_photo = request.FILES.get('aadhar_front_photo')
        aadhar_back_photo = request.FILES.get('aadhar_back_photo')
        pan_photo = request.FILES.get('pan_photo')
        
        from django.contrib.auth import get_user_model
        import uuid
        User = get_user_model()
        
        customer, created = User.objects.get_or_create(
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
        
        Lead.objects.create(
            customer=customer,
            interested_items=interested_items,
            salesperson=request.user
        )
        messages.success(request, 'Lead captured successfully.')
        return redirect('leads_list')
    return render(request, 'leads/add_lead.html')

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
