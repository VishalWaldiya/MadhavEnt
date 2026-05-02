from django.db import models
from inventory.models import ScooterModel, StockItem

class SaleRecord(models.Model):
    scooter_model = models.ForeignKey(ScooterModel, on_delete=models.PROTECT)
    chassis_number = models.ForeignKey(StockItem, on_delete=models.PROTECT, related_name='sale_as_scooter', limit_choices_to={'item_type': 'SCOOTER'})
    motor_number = models.CharField(max_length=100) # Often motor number is tracked alongside chassis
    charger = models.ForeignKey(StockItem, on_delete=models.PROTECT, related_name='sale_as_charger', limit_choices_to={'item_type': 'CHARGER'})
    
    customer = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    sale_date = models.DateTimeField(auto_now_add=True)
    financer = models.CharField(max_length=100, blank=True, null=True)
    
    gst_number = models.CharField(max_length=50, blank=True, null=True)
    taxable_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    misc = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return f"Sale: {self.customer.get_full_name() if self.customer else 'Unknown'} - {self.scooter_model.name}"

class SaleBattery(models.Model):
    sale_record = models.ForeignKey(SaleRecord, on_delete=models.CASCADE, related_name='batteries')
    battery = models.ForeignKey(StockItem, on_delete=models.PROTECT, limit_choices_to={'item_type': 'BATTERY'})
    misc = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return f"Battery for {self.sale_record}"

class SalePhoto(models.Model):
    sale_record = models.ForeignKey(SaleRecord, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to='sale_photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for {self.sale_record}"
