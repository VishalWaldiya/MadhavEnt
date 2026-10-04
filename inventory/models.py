from django.db import models
from django.db.models import Q
from core.models import SoftDeleteModel

class ScooterModel(SoftDeleteModel):
    name = models.CharField(max_length=100)
    watts = models.IntegerField(default=1200, help_text="Motor power in watts")
    charging_time = models.FloatField(default=4.0, help_text="Charging time in hours")
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Cost Price")
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Base Selling Price")
    
    # Battery configuration dependent ranges
    battery_lithium_60w_range = models.IntegerField(default=85, help_text="Range with 60V Lithium Battery (km)")
    battery_lithium_72w_range = models.IntegerField(default=115, help_text="Range with 72V Lithium Battery (km)")
    battery_lead_60w_range = models.IntegerField(default=55, help_text="Range with 60V Lead Acid Battery (km)")
    battery_lead_72w_range = models.IntegerField(default=70, help_text="Range with 72V Lead Acid Battery (km)")
    default_range_km = models.IntegerField(default=80, help_text="Default/Nominal Range (km)")
    
    description = models.TextField(blank=True, null=True)
    misc = models.JSONField(default=dict, blank=True, null=True)

    def get_range_for_battery(self, battery=None):
        """Calculate real-world estimated range based on battery chemistry and voltage."""
        if not battery:
            return self.default_range_km
        b_type = (battery.battery_type or '').upper()
        b_volt = (battery.voltage or '').upper()
        
        if 'LITHIUM' in b_type:
            if '72' in b_volt and self.battery_lithium_72w_range:
                return self.battery_lithium_72w_range
            elif self.battery_lithium_60w_range:
                return self.battery_lithium_60w_range
        elif 'LEAD' in b_type:
            if '72' in b_volt and self.battery_lead_72w_range:
                return self.battery_lead_72w_range
            elif self.battery_lead_60w_range:
                return self.battery_lead_60w_range
        return self.default_range_km

    def get_connected_resources(self, include_deleted=False):
        filter_func = (lambda manager: manager.all()) if include_deleted else (lambda manager: manager.filter(is_deleted=False))
        connected = []
        for scooter in filter_func(self.scooters):
            connected.append({
                'type': 'Scooter Unit',
                'id': scooter.id,
                'name': f"{self.name} - Chassis {scooter.chassis_number}",
                'object': scooter
            })
        return connected

    def __str__(self):
        return f"{self.name} (Base ₹{self.selling_price})"


class Scooter(SoftDeleteModel):
    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('SOLD', 'Sold'),
        ('DEFECTIVE', 'Defective'),
    )
    scooter_model = models.ForeignKey(ScooterModel, on_delete=models.CASCADE, related_name='scooters')
    chassis_number = models.CharField(max_length=100, unique=True)
    motor_number = models.CharField(max_length=100, blank=True, default='')
    color = models.CharField(max_length=50, blank=True, default='Standard')
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    purchase_date = models.DateField(auto_now_add=True)
    supplier_details = models.TextField(blank=True, null=True)
    misc = models.JSONField(default=dict, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.selling_price and self.scooter_model:
            self.selling_price = self.scooter_model.selling_price
        if not self.cost_price and self.scooter_model:
            self.cost_price = self.scooter_model.cost_price
        super().save(*args, **kwargs)

    def get_connected_resources(self, include_deleted=False):
        from sales.models import SaleScooterItem
        filter_func = (lambda manager: manager.all()) if include_deleted else (lambda manager: manager.filter(is_deleted=False))
        connected = []
        for item in filter_func(SaleScooterItem.objects.filter(scooter=self)):
            connected.append({
                'type': 'Sale Record',
                'id': item.sale_record.id,
                'name': f"Sale INV-{item.sale_record.id}",
                'object': item.sale_record
            })
        return connected

    def __str__(self):
        return f"{self.scooter_model.name} (Chassis: {self.chassis_number})"


class Battery(SoftDeleteModel):
    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('SOLD', 'Sold'),
        ('DEFECTIVE', 'Defective'),
    )
    BATTERY_TYPE_CHOICES = (
        ('LITHIUM', 'Lithium Ion / LFP'),
        ('LEAD_ACID', 'Lead Acid'),
        ('GRAPHENE', 'Graphene'),
    )
    VOLTAGE_CHOICES = (
        ('48V', '48V'),
        ('60V', '60V'),
        ('72V', '72V'),
    )
    name = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, unique=True)
    battery_type = models.CharField(max_length=20, choices=BATTERY_TYPE_CHOICES, default='LITHIUM')
    voltage = models.CharField(max_length=20, choices=VOLTAGE_CHOICES, default='60V')
    capacity_ah = models.CharField(max_length=20, default='30Ah', blank=True)
    
    # 2 different selling price categories: With Scooter and Without Scooter
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    price_with_scooter = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00,
        help_text="Bundled price when purchased alongside a scooter"
    )
    price_without_scooter = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00,
        help_text="Standard retail price when purchased independently"
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    purchase_date = models.DateField(auto_now_add=True)
    supplier_details = models.TextField(blank=True, null=True)
    misc = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return f"{self.name} [{self.serial_number}] ({self.voltage} {self.capacity_ah})"


class Charger(SoftDeleteModel):
    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('SOLD', 'Sold'),
        ('DEFECTIVE', 'Defective'),
    )
    VOLTAGE_CHOICES = (
        ('48V', '48V'),
        ('60V', '60V'),
        ('72V', '72V'),
    )
    name = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, unique=True)
    charger_type = models.CharField(max_length=50, default='Standard Fast Charger')
    voltage = models.CharField(max_length=20, choices=VOLTAGE_CHOICES, default='60V')
    
    # Cost price and 2 different selling prices (with scooter 1st charger is 0, without scooter retail)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    price_with_scooter = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00,
        help_text="Price with scooter (usually 0.00 for 1st bundled charger)"
    )
    price_without_scooter = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00,
        help_text="Standard retail price when bought standalone"
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    purchase_date = models.DateField(auto_now_add=True)
    supplier_details = models.TextField(blank=True, null=True)
    misc = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return f"{self.name} [{self.serial_number}] ({self.voltage})"


class SparePart(SoftDeleteModel):
    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('OUT_OF_STOCK', 'Out of Stock'),
    )
    name = models.CharField(max_length=150)
    part_number = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, blank=True, default='General Spare')
    quantity = models.PositiveIntegerField(default=1)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    purchase_date = models.DateField(auto_now_add=True)
    supplier_details = models.TextField(blank=True, null=True)
    misc = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.part_number}) - Qty: {self.quantity}"
