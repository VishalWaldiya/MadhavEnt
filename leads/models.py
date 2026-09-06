from django.db import models
from django.conf import settings
from inventory.models import ScooterModel
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
    interested_items = models.TextField(blank=True) # Summary or comma-separated item names
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    rejection_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def get_connected_resources(self, include_deleted=False):
        filter_func = (lambda manager: manager.all()) if include_deleted else (lambda manager: manager.filter(is_deleted=False))
        connected = []

        for req in filter_func(LeadRequirement.all_objects.filter(lead=self)):
            connected.append({
                'type': 'Lead Requirement',
                'id': req.id,
                'name': f"Requirement: {req.get_item_name()}",
                'object': req
            })

        for quote in filter_func(Quote.all_objects.filter(lead=self)):
            connected.append({
                'type': 'Quote',
                'id': quote.id,
                'name': f"Quote #{quote.id} for {self.customer.get_full_name() if self.customer else 'Unknown'}",
                'object': quote
            })
        return connected

    def __str__(self):
        return f"Lead: {self.customer.get_full_name() if self.customer else 'Unknown'}"


class LeadRequirement(SoftDeleteModel):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='requirements')
    scooter_model = models.ForeignKey(ScooterModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='lead_requirements')
    stock_item = models.ForeignKey('inventory.StockItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='lead_requirements')
    custom_item_name = models.CharField(max_length=255, blank=True, help_text="Used when item is not in DB inventory")
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
            return f"Scooter Model: {self.scooter_model.name}"
        elif self.stock_item:
            return f"{self.stock_item.get_item_type_display()}: {self.stock_item.name or self.stock_item.serial_number}"
        return self.custom_item_name or "Custom Item"

    def __str__(self):
        return f"{self.get_item_name()} (Qty: {self.quantity}, Total: ₹{self.total_price})"


class Quote(SoftDeleteModel):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='quotes')
    scooter_model = models.ForeignKey(ScooterModel, on_delete=models.SET_NULL, null=True, blank=True)
    battery = models.ForeignKey('inventory.StockItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='quoted_batteries')
    charger = models.ForeignKey('inventory.StockItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='quoted_chargers')
    quoted_price = models.DecimalField(max_digits=12, decimal_places=2)
    item_details = models.TextField()
    valid_until = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quote for {self.lead.customer.get_full_name() if self.lead and self.lead.customer else 'Unknown'}"
