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
    customer_name = models.CharField(max_length=100)
    contact = models.CharField(max_length=20)
    salesperson = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    interested_items = models.TextField(blank=True) # E.g., 'Looking for Scooter Model X'
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    
    # Finance and Identity Information
    aadhar_number = models.CharField(max_length=20, blank=True, null=True)
    pan_number = models.CharField(max_length=20, blank=True, null=True)
    aadhar_front_photo = models.ImageField(upload_to='leads/aadhar/', blank=True, null=True)
    aadhar_back_photo = models.ImageField(upload_to='leads/aadhar/', blank=True, null=True)
    pan_photo = models.ImageField(upload_to='leads/pan/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lead: {self.customer_name}"

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
