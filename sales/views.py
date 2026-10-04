from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal
import uuid

from .models import (
    SaleRecord, SaleScooterItem, SaleBatteryItem,
    SaleChargerItem, SaleSparePartItem, SalePhoto
)
from inventory.models import ScooterModel, Scooter, Battery, Charger, SparePart

User = get_user_model()

@login_required
def sales_list(request):
    sales = SaleRecord.objects.all().order_by('-sale_date')
    return render(request, 'sales/list.html', {'sales': sales})

@login_required
def add_sale(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Customer Details
                first_name = request.POST.get('first_name', '').strip()
                last_name = request.POST.get('last_name', '').strip()
                phone_number = request.POST.get('phone_number', '').strip()
                aadhar_number = request.POST.get('aadhar_number', '').strip()
                pan_number = request.POST.get('pan_number', '').strip()
                financer = request.POST.get('financer', '').strip()
                gst_number = request.POST.get('gst_number', '').strip()

                # Financials & Discounts
                subtotal_amount = Decimal(request.POST.get('subtotal_amount') or '0.00')
                discount_percentage = Decimal(request.POST.get('discount_percentage') or '0.00')
                discount_amount = Decimal(request.POST.get('discount_amount') or '0.00')
                discount_reason = request.POST.get('discount_reason', '').strip() or 'Discount'
                taxable_amount = Decimal(request.POST.get('taxable_amount') or '0.00')
                total_amount = Decimal(request.POST.get('total_amount') or '0.00')

                # Customer User resolution
                customer, created = User.all_objects.get_or_create(
                    phone_number=phone_number,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'role': 'CUSTOMER',
                        'username': f"cust_{phone_number}_{uuid.uuid4().hex[:6]}",
                    }
                )
                if not created:
                    if first_name: customer.first_name = first_name
                    if last_name: customer.last_name = last_name

                if aadhar_number: customer.aadhar_number = aadhar_number
                if pan_number: customer.pan_number = pan_number
                if request.FILES.get('aadhar_front_photo'): customer.aadhar_front_photo = request.FILES.get('aadhar_front_photo')
                if request.FILES.get('aadhar_back_photo'): customer.aadhar_back_photo = request.FILES.get('aadhar_back_photo')
                if request.FILES.get('pan_photo'): customer.pan_photo = request.FILES.get('pan_photo')
                customer.save()

                # Create Sale Record
                sale = SaleRecord.objects.create(
                    customer=customer,
                    salesperson=request.user,
                    financer=financer,
                    gst_number=gst_number,
                    subtotal_amount=subtotal_amount,
                    discount_percentage=discount_percentage,
                    discount_amount=discount_amount,
                    discount_reason=discount_reason,
                    taxable_amount=taxable_amount,
                    total_amount=total_amount
                )

                # Process Scooter Items (Vehicle)
                scooter_model_ids = request.POST.getlist('scooter_model')
                chassis_options = request.POST.getlist('chassis_number')
                motor_numbers = request.POST.getlist('motor_number')
                colors = request.POST.getlist('scooter_color')
                scooter_prices = request.POST.getlist('scooter_price')
                configured_battery_ids = request.POST.getlist('configured_battery')
                configured_ranges = request.POST.getlist('configured_range')

                for i in range(len(scooter_model_ids)):
                    m_id = scooter_model_ids[i]
                    if not m_id:
                        continue
                    model_obj = ScooterModel.objects.filter(id=m_id).first()
                    if not model_obj:
                        continue

                    chassis = chassis_options[i] if i < len(chassis_options) else ''
                    motor = motor_numbers[i] if i < len(motor_numbers) else ''
                    color = colors[i] if i < len(colors) else 'Standard'
                    u_price = Decimal(scooter_prices[i]) if (i < len(scooter_prices) and scooter_prices[i]) else model_obj.selling_price
                    
                    # Paired battery for range
                    bat_id = configured_battery_ids[i] if i < len(configured_battery_ids) else None
                    conf_bat = Battery.objects.filter(id=bat_id).first() if bat_id else None
                    
                    try:
                        rng = int(configured_ranges[i]) if (i < len(configured_ranges) and configured_ranges[i]) else model_obj.get_range_for_battery(conf_bat)
                    except (ValueError, TypeError):
                        rng = model_obj.get_range_for_battery(conf_bat)

                    # Check if chassis belongs to an existing available Scooter record
                    scooter_obj = None
                    if chassis:
                        scooter_obj = Scooter.objects.filter(chassis_number=chassis).first()
                        if scooter_obj:
                            scooter_obj.status = 'SOLD'
                            scooter_obj.save()

                    SaleScooterItem.objects.create(
                        sale_record=sale,
                        scooter_model=model_obj,
                        scooter=scooter_obj,
                        chassis_number=chassis,
                        motor_number=motor or (scooter_obj.motor_number if scooter_obj else ''),
                        color=color or (scooter_obj.color if scooter_obj else 'Standard'),
                        unit_price=u_price,
                        configured_battery=conf_bat,
                        configured_range_km=rng
                    )

                # Process Battery Items (Multiple allowed: With Scooter and/or Standalone)
                bat_ids = request.POST.getlist('bat_item_id')
                bat_names = request.POST.getlist('bat_item_name')
                bat_serials = request.POST.getlist('bat_item_serial')
                bat_categories = request.POST.getlist('bat_item_category')
                bat_quantities = request.POST.getlist('bat_item_qty')
                bat_prices = request.POST.getlist('bat_item_price')

                for i in range(len(bat_categories)):
                    b_cat = bat_categories[i] if i < len(bat_categories) else 'WITH_SCOOTER'
                    b_name = bat_names[i] if i < len(bat_names) else ''
                    b_serial = bat_serials[i] if i < len(bat_serials) else ''
                    b_id = bat_ids[i] if i < len(bat_ids) else None
                    
                    try: qty = max(1, int(bat_quantities[i])) if (i < len(bat_quantities) and bat_quantities[i]) else 1
                    except (ValueError, TypeError): qty = 1

                    try: price = Decimal(bat_prices[i]) if (i < len(bat_prices) and bat_prices[i]) else Decimal('0.00')
                    except Exception: price = Decimal('0.00')

                    bat_obj = None
                    if b_id:
                        bat_obj = Battery.objects.filter(id=b_id).first()
                        if bat_obj:
                            b_name = b_name or bat_obj.name
                            b_serial = b_serial or bat_obj.serial_number
                            bat_obj.status = 'SOLD'
                            bat_obj.save()

                    if b_name or bat_obj:
                        SaleBatteryItem.objects.create(
                            sale_record=sale,
                            battery=bat_obj,
                            battery_name=b_name or (bat_obj.name if bat_obj else 'Battery'),
                            serial_number=b_serial or (bat_obj.serial_number if bat_obj else ''),
                            sale_category=b_cat,
                            quantity=qty,
                            unit_price=price,
                            total_price=price * qty
                        )

                # Process Charger Items (Multiple allowed: With Scooter 1st Free, or Standalone)
                chg_ids = request.POST.getlist('chg_item_id')
                chg_names = request.POST.getlist('chg_item_name')
                chg_serials = request.POST.getlist('chg_item_serial')
                chg_categories = request.POST.getlist('chg_item_category')
                chg_quantities = request.POST.getlist('chg_item_qty')
                chg_prices = request.POST.getlist('chg_item_price')

                for i in range(len(chg_categories)):
                    c_cat = chg_categories[i] if i < len(chg_categories) else 'WITH_SCOOTER'
                    c_name = chg_names[i] if i < len(chg_names) else ''
                    c_serial = chg_serials[i] if i < len(chg_serials) else ''
                    c_id = chg_ids[i] if i < len(chg_ids) else None

                    try: qty = max(1, int(chg_quantities[i])) if (i < len(chg_quantities) and chg_quantities[i]) else 1
                    except (ValueError, TypeError): qty = 1

                    try: price = Decimal(chg_prices[i]) if (i < len(chg_prices) and chg_prices[i]) else Decimal('0.00')
                    except Exception: price = Decimal('0.00')

                    chg_obj = None
                    if c_id:
                        chg_obj = Charger.objects.filter(id=c_id).first()
                        if chg_obj:
                            c_name = c_name or chg_obj.name
                            c_serial = c_serial or chg_obj.serial_number
                            chg_obj.status = 'SOLD'
                            chg_obj.save()

                    if c_name or chg_obj:
                        SaleChargerItem.objects.create(
                            sale_record=sale,
                            charger=chg_obj,
                            charger_name=c_name or (chg_obj.name if chg_obj else 'Charger'),
                            serial_number=c_serial or (chg_obj.serial_number if chg_obj else ''),
                            sale_category=c_cat,
                            quantity=qty,
                            unit_price=price,
                            total_price=price * qty
                        )

                # Process Spare Parts Items
                spare_ids = request.POST.getlist('spare_item_id')
                spare_names = request.POST.getlist('spare_item_name')
                spare_quantities = request.POST.getlist('spare_item_qty')
                spare_prices = request.POST.getlist('spare_item_price')

                for i in range(len(spare_names)):
                    s_name = spare_names[i] if i < len(spare_names) else ''
                    s_id = spare_ids[i] if i < len(spare_ids) else None
                    if not s_name and not s_id:
                        continue

                    try: qty = max(1, int(spare_quantities[i])) if (i < len(spare_quantities) and spare_quantities[i]) else 1
                    except (ValueError, TypeError): qty = 1

                    try: price = Decimal(spare_prices[i]) if (i < len(spare_prices) and spare_prices[i]) else Decimal('0.00')
                    except Exception: price = Decimal('0.00')

                    spare_obj = None
                    if s_id:
                        spare_obj = SparePart.objects.filter(id=s_id).first()
                        if spare_obj:
                            s_name = s_name or spare_obj.name
                            if spare_obj.quantity >= qty:
                                spare_obj.quantity -= qty
                            else:
                                spare_obj.quantity = 0
                            if spare_obj.quantity == 0:
                                spare_obj.status = 'OUT_OF_STOCK'
                            spare_obj.save()

                    SaleSparePartItem.objects.create(
                        sale_record=sale,
                        spare_part=spare_obj,
                        part_name=s_name or (spare_obj.name if spare_obj else 'Spare Part'),
                        part_number=spare_obj.part_number if spare_obj else '',
                        quantity=qty,
                        unit_price=price,
                        total_price=price * qty
                    )

                # Handle Sale Photos
                sale_photos = request.FILES.getlist('sale_photos')
                for photo in sale_photos:
                    SalePhoto.objects.create(sale_record=sale, photo=photo)

                try:
                    from core.views import dispatch_push_notification
                    dispatch_push_notification(
                        category='SALE',
                        title='🛍️ New Sale Recorded',
                        message=f'Sale INV-{sale.id} recorded for ₹{total_amount}.',
                        target_url=f'/sales/invoice/{sale.id}/',
                        sender=request.user
                    )
                except Exception:
                    pass

                messages.success(request, f'Sale INV-{sale.id} recorded successfully!')
                return redirect('invoice_view', sale_id=sale.id)

        except Exception as e:
            messages.error(request, f"Error recording sale: {str(e)}")

    scooter_models = ScooterModel.objects.all()
    available_scooters = Scooter.objects.filter(status='AVAILABLE').select_related('scooter_model')
    available_batteries = Battery.objects.filter(status='AVAILABLE')
    available_chargers = Charger.objects.filter(status='AVAILABLE')
    available_spares = SparePart.objects.filter(status='AVAILABLE', quantity__gt=0)

    return render(request, 'sales/add_sale.html', {
        'scooter_models': scooter_models,
        'available_scooters': available_scooters,
        'available_batteries': available_batteries,
        'available_chargers': available_chargers,
        'available_spares': available_spares,
    })

@login_required
def invoice_view(request, sale_id):
    sale = get_object_or_404(SaleRecord.all_objects, id=sale_id)
    return render(request, 'sales/invoice.html', {'sale': sale})

@login_required
def search_asset(request):
    query = request.GET.get('q', '').strip()
    sale = None
    item_type = None
    item_obj = None

    if query:
        # Search by chassis/serial in 4 inventory tables
        scooter = Scooter.all_objects.filter(chassis_number__iexact=query).first()
        if scooter:
            item_obj = scooter
            item_type = 'Scooter'
            item_sale = SaleScooterItem.objects.filter(chassis_number__iexact=query).first()
            if item_sale:
                sale = item_sale.sale_record

        if not sale:
            bat = Battery.all_objects.filter(serial_number__iexact=query).first()
            if bat:
                item_obj = bat
                item_type = 'Battery'
                bat_sale = SaleBatteryItem.objects.filter(serial_number__iexact=query).first()
                if bat_sale:
                    sale = bat_sale.sale_record

        if not sale:
            chg = Charger.all_objects.filter(serial_number__iexact=query).first()
            if chg:
                item_obj = chg
                item_type = 'Charger'
                chg_sale = SaleChargerItem.objects.filter(serial_number__iexact=query).first()
                if chg_sale:
                    sale = chg_sale.sale_record

        if not sale:
            spare = SparePart.all_objects.filter(part_number__iexact=query).first()
            if spare:
                item_obj = spare
                item_type = 'Spare Part'
                sp_sale = SaleSparePartItem.objects.filter(part_number__iexact=query).first()
                if sp_sale:
                    sale = sp_sale.sale_record

    return render(request, 'sales/search.html', {
        'query': query,
        'item': item_obj,
        'item_type': item_type,
        'sale': sale
    })

@login_required
def gst_report(request):
    sales = SaleRecord.objects.exclude(gst_number__isnull=True).exclude(gst_number__exact='')
    total_taxable = sum(s.taxable_amount for s in sales if s.taxable_amount)
    total_amt = sum(s.total_amount for s in sales if s.total_amount)
    return render(request, 'sales/gst_report.html', {
        'sales': sales,
        'total_taxable': total_taxable,
        'total_amount': total_amt
    })

@login_required
def delete_sale(request, sale_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Only administrators can delete sale records.')
        return redirect('sales_list')
    sale = get_object_or_404(SaleRecord, id=sale_id)
    if request.method == 'POST':
        sale.delete()
        messages.success(request, f'Sale record INV-{sale.id} moved to Recycle Bin.')
    return redirect('sales_list')
