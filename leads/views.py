from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from decimal import Decimal
import uuid

from .models import Lead, Quote, QuoteItem, LeadRequirement
from inventory.models import ScooterModel, Battery, Charger, SparePart
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def leads_list(request):
    leads = Lead.objects.all().order_by('-created_at')
    return render(request, 'leads/list.html', {'leads': leads})

@login_required
def add_lead(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        interested_items_text = request.POST.get('interested_items', '').strip()
        
        aadhar_number = request.POST.get('aadhar_number', '').strip()
        pan_number = request.POST.get('pan_number', '').strip()
        aadhar_front_photo = request.FILES.get('aadhar_front_photo')
        aadhar_back_photo = request.FILES.get('aadhar_back_photo')
        pan_photo = request.FILES.get('pan_photo')
        
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
        if aadhar_front_photo: customer.aadhar_front_photo = aadhar_front_photo
        if aadhar_back_photo: customer.aadhar_back_photo = aadhar_back_photo
        if pan_photo: customer.pan_photo = pan_photo
        customer.save()
        
        lead = Lead.objects.create(
            customer=customer,
            interested_items=interested_items_text,
            salesperson=request.user
        )
        lead.log_history(
            action_type='CREATED',
            title='Lead Captured',
            details=f"Lead recorded by {request.user.get_full_name() or request.user.username}. Interested in: {interested_items_text or 'General Inquiry'}",
            user=request.user
        )

        messages.success(request, 'Lead captured successfully.')
        return redirect('lead_detail', lead_id=lead.id)

    return render(request, 'leads/add_lead.html')

@login_required
def lead_detail(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    history_entries = lead.history.all().order_by('-created_at')
    quotes = lead.quotes.all().order_by('-created_at')
    return render(request, 'leads/detail.html', {
        'lead': lead,
        'history_entries': history_entries,
        'quotes': quotes,
    })

@login_required
def edit_lead(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    sales_users = User.objects.filter(role__in=['ADMIN', 'SALES'], is_active=True)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        aadhar_number = request.POST.get('aadhar_number', '').strip()
        pan_number = request.POST.get('pan_number', '').strip()

        salesperson_id = request.POST.get('salesperson')
        new_status = request.POST.get('status', lead.status)
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        interested_items = request.POST.get('interested_items', '').strip()
        edit_notes = request.POST.get('edit_notes', '').strip()

        changes = []

        # Customer fields update
        if lead.customer:
            cust = lead.customer
            if first_name and cust.first_name != first_name:
                changes.append(f"First Name changed: '{cust.first_name}' → '{first_name}'")
                cust.first_name = first_name
            if last_name and cust.last_name != last_name:
                changes.append(f"Last Name changed: '{cust.last_name}' → '{last_name}'")
                cust.last_name = last_name
            if phone_number and cust.phone_number != phone_number:
                changes.append(f"Phone changed: '{cust.phone_number}' → '{phone_number}'")
                cust.phone_number = phone_number
            if aadhar_number != (cust.aadhar_number or ''):
                changes.append(f"Aadhar number updated")
                cust.aadhar_number = aadhar_number
            if pan_number != (cust.pan_number or ''):
                changes.append(f"PAN number updated")
                cust.pan_number = pan_number
            if request.FILES.get('aadhar_front_photo'):
                cust.aadhar_front_photo = request.FILES.get('aadhar_front_photo')
                changes.append("Aadhar Front photo uploaded")
            if request.FILES.get('aadhar_back_photo'):
                cust.aadhar_back_photo = request.FILES.get('aadhar_back_photo')
                changes.append("Aadhar Back photo uploaded")
            if request.FILES.get('pan_photo'):
                cust.pan_photo = request.FILES.get('pan_photo')
                changes.append("PAN photo uploaded")
            cust.save()

        # Salesperson reassignment
        if salesperson_id:
            try:
                new_sp = User.objects.get(id=salesperson_id)
                if lead.salesperson != new_sp:
                    old_sp_name = lead.salesperson.get_full_name() if lead.salesperson else 'Unassigned'
                    changes.append(f"Salesperson reassigned from {old_sp_name} to {new_sp.get_full_name()}")
                    lead.salesperson = new_sp
            except User.DoesNotExist:
                pass

        # Status update
        old_status = lead.status
        if new_status and new_status != lead.status:
            changes.append(f"Status changed from {lead.get_status_display()} to {dict(Lead.STATUS_CHOICES).get(new_status, new_status)}")
            lead.status = new_status
            if new_status == 'REJECTED':
                lead.rejection_reason = rejection_reason
        elif new_status == 'REJECTED' and rejection_reason != (lead.rejection_reason or ''):
            lead.rejection_reason = rejection_reason
            changes.append(f"Rejection reason updated: {rejection_reason}")

        # Interested items update
        if interested_items != lead.interested_items:
            changes.append("Interested items / requirements updated")
            lead.interested_items = interested_items

        lead.save()

        # Save history entry
        if changes or edit_notes:
            details_text = "\n".join(changes)
            if edit_notes:
                details_text += f"\nNote: {edit_notes}" if details_text else edit_notes
            lead.log_history(
                action_type='STATUS_CHANGE' if (new_status != old_status) else 'EDITED',
                title='Lead Details Updated' if (new_status == old_status) else f'Status Changed to {lead.get_status_display()}',
                details=details_text or 'Lead details updated.',
                user=request.user
            )

        messages.success(request, f'Lead for {lead.customer.get_full_name() if lead.customer else "Customer"} updated successfully.')
        return redirect('lead_detail', lead_id=lead.id)

    return render(request, 'leads/edit_lead.html', {
        'lead': lead,
        'sales_users': sales_users,
    })

@login_required
def add_lead_note(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    if request.method == 'POST':
        note_type = request.POST.get('note_type', 'Follow-up')
        content = request.POST.get('content', '').strip()
        if content:
            lead.log_history(
                action_type='NOTE_ADDED',
                title=f"{note_type} Recorded",
                details=content,
                user=request.user
            )
            messages.success(request, 'Interaction note added to lead history timeline.')
    return redirect('lead_detail', lead_id=lead.id)

@login_required
def update_lead_status(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        reason = request.POST.get('reason', '').strip()
        if new_status and new_status != lead.status:
            old_display = lead.get_status_display()
            lead.status = new_status
            if new_status == 'REJECTED':
                lead.rejection_reason = reason
            lead.save()
            details = f"Status updated from {old_display} to {lead.get_status_display()}."
            if reason:
                details += f" Reason / Remarks: {reason}"
            lead.log_history(
                action_type='STATUS_CHANGE',
                title=f"Status Changed to {lead.get_status_display()}",
                details=details,
                user=request.user
            )
            messages.success(request, f'Lead status updated to {lead.get_status_display()}.')
    return redirect('lead_detail', lead_id=lead.id)

@login_required
def add_quote(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    if request.method == 'POST':
        subtotal_amount = Decimal(request.POST.get('subtotal_amount') or '0.00')
        discount_percentage = Decimal(request.POST.get('discount_percentage') or '0.00')
        discount_amount = Decimal(request.POST.get('discount_amount') or '0.00')
        discount_reason = request.POST.get('discount_reason', '').strip() or 'Quotation Discount'
        quoted_price = Decimal(request.POST.get('quoted_price') or '0.00')
        valid_until = request.POST.get('valid_until')
        item_details = request.POST.get('item_details', '')

        quote = Quote.objects.create(
            lead=lead,
            subtotal_amount=subtotal_amount,
            discount_percentage=discount_percentage,
            discount_amount=discount_amount,
            discount_reason=discount_reason,
            quoted_price=quoted_price,
            valid_until=valid_until,
            item_details=item_details
        )

        # Process Quote Items across 4 categories
        item_types = request.POST.getlist('item_type')
        item_names = request.POST.getlist('item_name')
        item_cats = request.POST.getlist('item_category')
        item_qtys = request.POST.getlist('item_quantity')
        item_prices = request.POST.getlist('item_unit_price')

        for i in range(len(item_names)):
            name = item_names[i] if i < len(item_names) else ''
            if not name:
                continue
            itype = item_types[i] if i < len(item_types) else 'OTHER'
            icat = item_cats[i] if i < len(item_cats) else 'WITH_SCOOTER'
            try: qty = int(item_qtys[i]) if (i < len(item_qtys) and item_qtys[i]) else 1
            except: qty = 1
            try: price = Decimal(item_prices[i]) if (i < len(item_prices) and item_prices[i]) else Decimal('0.00')
            except: price = Decimal('0.00')

            QuoteItem.objects.create(
                quote=quote,
                item_type=itype,
                item_name=name,
                sale_category=icat,
                quantity=qty,
                unit_price=price,
                total_price=price * qty
            )

        lead.log_history(
            action_type='QUOTE_ADDED',
            title=f"Quotation #{quote.id} Created",
            details=f"Quote created: ₹{quote.quoted_price} (Subtotal: ₹{quote.subtotal_amount}, Discount: ₹{quote.discount_amount} '{quote.discount_reason}'). Valid until: {quote.valid_until}.",
            user=request.user
        )

        messages.success(request, f'Quotation #{quote.id} created successfully for {lead.customer.get_full_name() if lead.customer else "Lead"}.')
        return redirect('lead_detail', lead_id=lead.id)

    scooters = ScooterModel.objects.all()
    batteries = Battery.objects.filter(status='AVAILABLE')
    chargers = Charger.objects.filter(status='AVAILABLE')
    spare_parts = SparePart.objects.filter(status='AVAILABLE')

    return render(request, 'leads/add_quote.html', {
        'lead': lead,
        'scooters': scooters,
        'batteries': batteries,
        'chargers': chargers,
        'spare_parts': spare_parts,
    })

@login_required
def reject_lead(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    if request.method == 'POST':
        reason = request.POST.get('rejection_reason', '')
        lead.status = 'REJECTED'
        lead.rejection_reason = reason
        lead.save()

        lead.log_history(
            action_type='REJECTED',
            title='Lead Rejected',
            details=f"Rejection Reason: {reason or 'No reason specified'}",
            user=request.user
        )

        messages.success(request, f'Lead for {lead.customer.get_full_name() if lead.customer else "Customer"} has been rejected.')
    return redirect('lead_detail', lead_id=lead.id)

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
        messages.success(request, f'Lead for {cust_name} moved to Recycle Bin.')
    return redirect('leads_list')
