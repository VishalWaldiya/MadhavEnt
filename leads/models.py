from django.db import models
from django.conf import settings
from inventory.models import ScooterModel

class Lead(models.Model):
    STATUS_CHOICES = (
        ('NEW', 'New'),
        ('IN_PROGRESS', 'In Progress'),
        ('CONVERTED', 'Converted'),
        ('LOST', 'Lost'),
    )
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    salesperson = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='managed_leads')
    interested_items = models.TextField(blank=True) # E.g., 'Looking for Scooter Model X'
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lead: {self.customer.get_full_name() if self.customer else 'Unknown'}"

class Quote(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='quotes')
    scooter_model = models.ForeignKey(ScooterModel, on_delete=models.SET_NULL, null=True, blank=True)
    battery = models.ForeignKey('inventory.StockItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='quoted_batteries')
    charger = models.ForeignKey('inventory.StockItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='quoted_chargers')
    quoted_price = models.DecimalField(max_digits=12, decimal_places=2)
    item_details = models.TextField()
    valid_until = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quote for {self.lead.customer_name}"
