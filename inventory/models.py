from django.db import models
from core.models import SoftDeleteModel

class ScooterModel(SoftDeleteModel):
    name = models.CharField(max_length=100)
    range_km = models.IntegerField()
    watts = models.IntegerField()
    charging_time = models.FloatField()
    last_price = models.DecimalField(max_digits=10, decimal_places=2)

    # Battery variants and their ranges
    battery_lithium_60w_range = models.IntegerField(null=True, blank=True, help_text="Range with 60W Lithium Battery")
    battery_lithium_72w_range = models.IntegerField(null=True, blank=True, help_text="Range with 72W Lithium Battery")
    battery_lead_60w_range = models.IntegerField(null=True, blank=True, help_text="Range with 60W Lead Battery")
    battery_lead_72w_range = models.IntegerField(null=True, blank=True, help_text="Range with 72W Lead Battery")
    
    misc = models.JSONField(default=dict, blank=True, null=True)

    def get_connected_resources(self, include_deleted=False):
        from sales.models import SaleRecord
        from leads.models import Quote

        filter_func = (lambda manager: manager.all()) if include_deleted else (lambda manager: manager.filter(is_deleted=False))
        connected = []

        for item in filter_func(StockItem.all_objects.filter(scooter_model=self)):
            connected.append({
                'type': 'Stock Item',
                'id': item.id,
                'name': f"{item.get_item_type_display()} - {item.serial_number}",
                'object': item
            })
        for sale in filter_func(SaleRecord.all_objects.filter(scooter_model=self)):
            connected.append({
                'type': 'Sale Record',
                'id': sale.id,
                'name': f"Sale INV-{sale.id}",
                'object': sale
            })
        for quote in filter_func(Quote.all_objects.filter(scooter_model=self)):
            connected.append({
                'type': 'Quote',
                'id': quote.id,
                'name': f"Quote #{quote.id} for {quote.lead}",
                'object': quote
            })
        return connected

    def __str__(self):
        return self.name

class StockItem(SoftDeleteModel):
    TYPE_CHOICES = (
        ('SCOOTER', 'Electric Scooter'),
        ('BATTERY', 'Battery'),
        ('CHARGER', 'Battery Charger'),
        ('SPARE', 'Spare Part'),
    )
    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('SOLD', 'Sold'),
        ('DEFECTIVE', 'Defective'),
    )
    BATTERY_TYPE_CHOICES = (
        ('LITHIUM', 'Lithium Battery'),
        ('LEAD', 'Lead Battery'),
    )
    WATTAGE_CHOICES = (
        ('60W', '60 Watt'),
        ('72W', '72 Watt'),
    )
    item_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    scooter_model = models.ForeignKey(ScooterModel, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100) # Could be spare part name
    serial_number = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    purchase_date = models.DateField(auto_now_add=True)
    supplier_details = models.TextField(blank=True, null=True)
    
    battery_type = models.CharField(max_length=20, choices=BATTERY_TYPE_CHOICES, null=True, blank=True)
    wattage = models.CharField(max_length=20, choices=WATTAGE_CHOICES, null=True, blank=True)
    
    misc = models.JSONField(default=dict, blank=True, null=True)

    def get_connected_resources(self, include_deleted=False):
        from sales.models import SaleRecord
        from leads.models import Quote
        from django.db.models import Q

        filter_func = (lambda manager: manager.all()) if include_deleted else (lambda manager: manager.filter(is_deleted=False))
        connected = []

        for sale in filter_func(SaleRecord.all_objects.filter(Q(chassis_number=self) | Q(charger=self))):
            connected.append({
                'type': 'Sale Record',
                'id': sale.id,
                'name': f"Sale INV-{sale.id}",
                'object': sale
            })
        for quote in filter_func(Quote.all_objects.filter(Q(battery=self) | Q(charger=self))):
            connected.append({
                'type': 'Quote',
                'id': quote.id,
                'name': f"Quote #{quote.id} for {quote.lead}",
                'object': quote
            })
        return connected

    def __str__(self):
        return f"{self.item_type} - {self.serial_number}"
