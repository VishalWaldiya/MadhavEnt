from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import SaleRecord, SaleBattery
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
        customer_name = request.POST.get('customer_name')
        customer_contact = request.POST.get('customer_contact')
        financer = request.POST.get('financer')
        gst_number = request.POST.get('gst_number')
        taxable_amount = request.POST.get('taxable_amount')
        total_amount = request.POST.get('total_amount')
        
        battery_ids = request.POST.getlist('batteries')
        
        scooter_model = ScooterModel.objects.get(id=scooter_model_id)
        chassis = StockItem.objects.get(id=chassis_id)
        charger = StockItem.objects.get(id=charger_id)

        sale = SaleRecord.objects.create(
            scooter_model=scooter_model,
            chassis_number=chassis,
            motor_number=motor_number,
            charger=charger,
            customer_name=customer_name,
            customer_contact=customer_contact,
            financer=financer,
            gst_number=gst_number,
            taxable_amount=taxable_amount,
            total_amount=total_amount
        )
        
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
def gst_report(request):
    sales = SaleRecord.objects.exclude(gst_number__isnull=True).exclude(gst_number__exact='')
    total_taxable = sum(s.taxable_amount for s in sales if s.taxable_amount)
    total_amt = sum(s.total_amount for s in sales if s.total_amount)
    return render(request, 'sales/gst_report.html', {'sales': sales, 'total_taxable': total_taxable, 'total_amount': total_amt})

