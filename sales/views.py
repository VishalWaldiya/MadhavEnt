from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import SaleRecord, SaleBattery, SalePhoto
from inventory.models import ScooterModel, StockItem
from django.contrib import messages

@login_required
def sales_list(request):
    sales = SaleRecord.objects.all().order_by('-sale_date')
    return render(request, 'sales/list.html', {'sales': sales})

@login_required
def add_sale(request):
    if request.method == 'POST':
        scooter_model_id = request.POST.get('scooter_model')
        chassis_id = request.POST.get('chassis_number')
        motor_number = request.POST.get('motor_number')
        charger_id = request.POST.get('charger')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone_number = request.POST.get('phone_number', '')
        financer = request.POST.get('financer')
        taxable_amount = request.POST.get('taxable_amount')
        total_amount = request.POST.get('total_amount')
        gst_number = request.POST.get('gst_number')
        
        aadhar_number = request.POST.get('aadhar_number')
        pan_number = request.POST.get('pan_number')
        aadhar_front_photo = request.FILES.get('aadhar_front_photo')
        aadhar_back_photo = request.FILES.get('aadhar_back_photo')
        pan_photo = request.FILES.get('pan_photo')
        
        battery_ids = request.POST.getlist('batteries')
        
        scooter_model = get_object_or_404(ScooterModel, id=scooter_model_id)
        chassis = get_object_or_404(StockItem, id=chassis_id)
        charger = get_object_or_404(StockItem, id=charger_id)
        
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
        
        sale = SaleRecord.objects.create(
            scooter_model=scooter_model,
            chassis_number=chassis,
            motor_number=motor_number,
            charger=charger,
            customer=customer,
            financer=financer,
            gst_number=gst_number,
            taxable_amount=taxable_amount,
            total_amount=total_amount
        )
        
        # Handle Sale Photos
        sale_photos = request.FILES.getlist('sale_photos')
        for photo in sale_photos:
            SalePhoto.objects.create(sale_record=sale, photo=photo)
        
        for b_id in battery_ids:
            if b_id:
                battery = StockItem.objects.get(id=b_id)
                SaleBattery.objects.create(sale_record=sale, battery=battery)
                battery.status = 'SOLD'
                battery.save()
                
        chassis.status = 'SOLD'
        chassis.save()
        charger.status = 'SOLD'
        charger.save()

        messages.success(request, 'Sale recorded successfully!')
        return redirect('sales_list')
        
    models = ScooterModel.objects.all()
    available_scooters = StockItem.objects.filter(item_type='SCOOTER', status='AVAILABLE')
    available_batteries = StockItem.objects.filter(item_type='BATTERY', status='AVAILABLE')
    available_chargers = StockItem.objects.filter(item_type='CHARGER', status='AVAILABLE')
    
    return render(request, 'sales/add_sale.html', {
        'models': models,
        'available_scooters': available_scooters,
        'available_batteries': available_batteries,
        'available_chargers': available_chargers
    })

@login_required
def search_asset(request):
    query = request.GET.get('q')
    item = None
    sale = None
    if query:
        item = StockItem.objects.filter(serial_number__icontains=query).first()
        if not item:
            item = StockItem.objects.filter(name__icontains=query).first()
        if item:
            sale = SaleRecord.objects.filter(chassis_number=item).first()
            if not sale:
                sb = SaleBattery.objects.filter(battery=item).first()
                if sb:
                    sale = sb.sale_record
            if not sale:
                sale = SaleRecord.objects.filter(charger=item).first()
    return render(request, 'sales/search.html', {'query': query, 'item': item, 'sale': sale})

@login_required
def invoice_view(request, sale_id):
    sale = get_object_or_404(SaleRecord, id=sale_id)
    return render(request, 'sales/invoice.html', {'sale': sale})

@login_required
def gst_report(request):
    sales = SaleRecord.objects.exclude(gst_number__isnull=True).exclude(gst_number__exact='')
    total_taxable = sum(s.taxable_amount for s in sales if s.taxable_amount)
    total_amt = sum(s.total_amount for s in sales if s.total_amount)
    return render(request, 'sales/gst_report.html', {'sales': sales, 'total_taxable': total_taxable, 'total_amount': total_amt})

