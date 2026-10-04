from django.db import models
from core.models import SoftDeleteModel
from inventory.models import ScooterModel, Scooter, Battery, Charger, SparePart

class SaleRecord(SoftDeleteModel):
    customer = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    salesperson = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='recorded_sales')
    sale_date = models.DateTimeField(auto_now_add=True)
    financer = models.CharField(max_length=100, blank=True, null=True)
    gst_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Financials & Discounts
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Gross total before discounts")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Discount percentage (%)")
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Total discount in Rupees")
    discount_reason = models.CharField(max_length=200, blank=True, null=True, help_text="e.g. Diwali Discount, Family and Friends Discount")
    
    taxable_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Final bill amount")
    
    misc = models.JSONField(default=dict, blank=True, null=True)

    @property
    def primary_scooter(self):
        first_item = self.scooter_items.first()
        return first_item.scooter_model if first_item else None

    def __str__(self):
        cust = self.customer.get_full_name() if self.customer else 'Unknown'
        return f"Sale INV-{self.id}: {cust} - ₹{self.total_amount}"


class SaleScooterItem(models.Model):
    sale_record = models.ForeignKey(SaleRecord, on_delete=models.CASCADE, related_name='scooter_items')
    scooter_model = models.ForeignKey(ScooterModel, on_delete=models.PROTECT)
    scooter = models.ForeignKey(Scooter, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_as_scooter')
    chassis_number = models.CharField(max_length=100)
    motor_number = models.CharField(max_length=100, blank=True, default='')
    color = models.CharField(max_length=50, blank=True, default='Standard')
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Range is dynamically computed and locked in for the specific battery pairing
    configured_battery = models.ForeignKey(Battery, on_delete=models.SET_NULL, null=True, blank=True)
    configured_range_km = models.IntegerField(null=True, blank=True, help_text="Configured range with chosen battery")

    def __str__(self):
        return f"{self.scooter_model.name} (Chassis: {self.chassis_number})"


class SaleBatteryItem(models.Model):
    CATEGORY_CHOICES = (
        ('WITH_SCOOTER', 'With Scooter (Bundled Price)'),
        ('WITHOUT_SCOOTER', 'Without Scooter (Standalone Retail)'),
    )
    sale_record = models.ForeignKey(SaleRecord, on_delete=models.CASCADE, related_name='battery_items')
    battery = models.ForeignKey(Battery, on_delete=models.SET_NULL, null=True, blank=True)
    battery_name = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, blank=True, default='')
    sale_category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='WITH_SCOOTER')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.battery_name} ({self.get_sale_category_display()}) x {self.quantity}"


class SaleChargerItem(models.Model):
    CATEGORY_CHOICES = (
        ('WITH_SCOOTER', 'With Scooter (1st Free)'),
        ('WITHOUT_SCOOTER', 'Without Scooter (Standalone Retail)'),
    )
    sale_record = models.ForeignKey(SaleRecord, on_delete=models.CASCADE, related_name='charger_items')
    charger = models.ForeignKey(Charger, on_delete=models.SET_NULL, null=True, blank=True)
    charger_name = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, blank=True, default='')
    sale_category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='WITH_SCOOTER')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.charger_name} ({self.get_sale_category_display()}) x {self.quantity}"


class SaleSparePartItem(models.Model):
    sale_record = models.ForeignKey(SaleRecord, on_delete=models.CASCADE, related_name='spare_part_items')
    spare_part = models.ForeignKey(SparePart, on_delete=models.SET_NULL, null=True, blank=True)
    part_name = models.CharField(max_length=150)
    part_number = models.CharField(max_length=100, blank=True, default='')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.part_name} x {self.quantity}"


class SalePhoto(models.Model):
    sale_record = models.ForeignKey(SaleRecord, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to='sale_photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for INV-{self.sale_record.id}"
