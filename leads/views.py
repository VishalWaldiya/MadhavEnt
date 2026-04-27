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
        customer_name = request.POST.get('customer_name')
        contact = request.POST.get('contact')
        interested_items = request.POST.get('interested_items')
        
        aadhar_number = request.POST.get('aadhar_number')
        pan_number = request.POST.get('pan_number')
        aadhar_front_photo = request.FILES.get('aadhar_front_photo')
        aadhar_back_photo = request.FILES.get('aadhar_back_photo')
        pan_photo = request.FILES.get('pan_photo')
        
        Lead.objects.create(
            customer_name=customer_name,
            contact=contact,
            salesperson=request.user,
            interested_items=interested_items,
            aadhar_number=aadhar_number,
            pan_number=pan_number,
            aadhar_front_photo=aadhar_front_photo,
            aadhar_back_photo=aadhar_back_photo,
            pan_photo=pan_photo
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
