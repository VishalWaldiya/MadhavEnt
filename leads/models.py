from django.db import models
from django.conf import settings
from inventory.models import ScooterModel, Scooter, Battery, Charger, SparePart
from core.models import SoftDeleteModel

class Lead(SoftDeleteModel):
    STATUS_CHOICES = (
        ('NEW', 'New'),
        ('IN_PROGRESS', 'In Progress'),
        ('CONVERTED', 'Converted'),
        ('LOST', 'Lost'),
        ('REJECTED', 'Rejected'),
    )
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    salesperson = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='managed_leads')
    interested_items = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_connected_resources(self, include_deleted=False):
        filter_func = (lambda manager: manager.all()) if include_deleted else (lambda manager: manager.filter(is_deleted=False))
        connected = []
        for req in filter_func(self.requirements):
            connected.append({
                'type': 'Lead Requirement',
                'id': req.id,
                'name': f"Requirement: {req.get_item_name()}",
                'object': req
            })
        for quote in filter_func(self.quotes):
            connected.append({
                'type': 'Quote',
                'id': quote.id,
                'name': f"Quote #{quote.id} for {self.customer.get_full_name() if self.customer else 'Unknown'}",
                'object': quote
            })
        return connected

    def log_history(self, action_type, title, details='', user=None):
        return LeadHistory.objects.create(
            lead=self,
            action_type=action_type,
            title=title,
            details=details,
            performed_by=user
        )

    def __str__(self):
        return f"Lead: {self.customer.get_full_name() if self.customer else 'Unknown'}"


class LeadRequirement(SoftDeleteModel):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='requirements')
    scooter_model = models.ForeignKey(ScooterModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='lead_requirements')
    battery = models.ForeignKey(Battery, on_delete=models.SET_NULL, null=True, blank=True)
    charger = models.ForeignKey(Charger, on_delete=models.SET_NULL, null=True, blank=True)
    spare_part = models.ForeignKey(SparePart, on_delete=models.SET_NULL, null=True, blank=True)
    custom_item_name = models.CharField(max_length=255, blank=True, help_text="Used when item is custom")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def get_item_name(self):
        if self.scooter_model:
            return f"Scooter: {self.scooter_model.name}"
        if self.battery:
            return f"Battery: {self.battery.name}"
        if self.charger:
            return f"Charger: {self.charger.name}"
        if self.spare_part:
            return f"Spare Part: {self.spare_part.name}"
        return self.custom_item_name or "Custom Item"

    def __str__(self):
        return f"{self.get_item_name()} (Qty: {self.quantity}, Total: ₹{self.total_price})"


class Quote(SoftDeleteModel):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='quotes')
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_reason = models.CharField(max_length=200, blank=True, null=True)
    quoted_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    item_details = models.TextField(blank=True, null=True)
    valid_until = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quote #{self.id} for {self.lead.customer.get_full_name() if self.lead and self.lead.customer else 'Unknown'} (₹{self.quoted_price})"


class QuoteItem(models.Model):
    ITEM_TYPES = (
        ('SCOOTER', 'Scooter Model'),
        ('BATTERY', 'Battery'),
        ('CHARGER', 'Charger'),
        ('SPARE', 'Spare Part'),
        ('OTHER', 'Other Accessory'),
    )
    CATEGORY_CHOICES = (
        ('WITH_SCOOTER', 'With Scooter'),
        ('WITHOUT_SCOOTER', 'Without Scooter'),
    )
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES, default='SCOOTER')
    item_name = models.CharField(max_length=200)
    sale_category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='WITH_SCOOTER', blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    notes = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class LeadHistory(models.Model):
    ACTION_TYPES = (
        ('CREATED', 'Lead Created'),
        ('STATUS_CHANGE', 'Status Changed'),
        ('EDITED', 'Lead Details Edited'),
        ('NOTE_ADDED', 'Interaction / Note Added'),
        ('QUOTE_ADDED', 'Quotation Generated'),
        ('REJECTED', 'Lead Rejected'),
        ('RESTORED', 'Lead Restored'),
    )
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='history')
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES, default='NOTE_ADDED')
    title = models.CharField(max_length=255)
    details = models.TextField(blank=True, null=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.lead}: {self.title} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

