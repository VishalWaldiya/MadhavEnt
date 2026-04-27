import os
import django
import random
from decimal import Decimal
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from inventory.models import ScooterModel, StockItem
from sales.models import SaleRecord, SaleBattery
from leads.models import Lead, Quote
from django.utils import timezone

User = get_user_model()

print("Generating dummy data...")

# Create Sales Users
sales_ids = []
for i in range(1, 4):
    username = f'sales{i}'
    user, created = User.objects.get_or_create(username=username, defaults={
        'role': 'SALES'
    })
    if created:
        user.set_password('sales123')
        user.save()
    sales_ids.append(user)

scooter_data = [
    {"name": "EcoBolt 100", "range_km": 80, "watts": 1200, "charging_time": 4.5, "last_price": 65000.00},
    {"name": "VoltMax Pro", "range_km": 120, "watts": 2500, "charging_time": 6.0, "last_price": 95000.00},
    {"name": "CityGlide E", "range_km": 60, "watts": 800, "charging_time": 3.0, "last_price": 45000.00},
]
models_list = []
for sd in scooter_data:
    sm, _ = ScooterModel.objects.get_or_create(name=sd['name'], defaults=sd)
    models_list.append(sm)

# Create Stock
for sm in models_list:
    for i in range(5):
        StockItem.objects.get_or_create(serial_number=f"SC-{sm.id}-E{i}982", defaults={
            "item_type": "SCOOTER", "scooter_model": sm, "status": "AVAILABLE"
        })

for i in range(30):
    StockItem.objects.get_or_create(serial_number=f"BAT-Lithium-X{i}", defaults={
        "item_type": "BATTERY", "name": "Lithium 60V 30Ah", "status": "AVAILABLE"
    })

for i in range(20):
    StockItem.objects.get_or_create(serial_number=f"CHG-Fast-{i}", defaults={
        "item_type": "CHARGER", "name": "Fast Charger 60V", "status": "AVAILABLE"
    })

# Sales
customers = ["Ravi Kumar", "Priya Sharma", "Amit Singh", "Neha Gupta", "Vikram Patel"]
available_scooters = list(StockItem.objects.filter(item_type="SCOOTER", status="AVAILABLE"))
available_batteries = list(StockItem.objects.filter(item_type="BATTERY", status="AVAILABLE"))
available_chargers = list(StockItem.objects.filter(item_type="CHARGER", status="AVAILABLE"))

for i in range(5):
    if not available_scooters or len(available_batteries) < 2 or not available_chargers:
        break
        
    scooter = available_scooters.pop()
    charger = available_chargers.pop()
    battery1 = available_batteries.pop()
    battery2 = available_batteries.pop()
    
    sale_date = timezone.now().date() - timedelta(days=random.randint(1, 10))
    customer = random.choice(customers)
    
    sale, created = SaleRecord.objects.get_or_create(chassis_number=scooter, defaults={
        "charger": charger,
        "scooter_model": scooter.scooter_model,
        "customer_name": customer,
        "customer_contact": f"9876543{random.randint(100, 999)}",
        "sale_date": sale_date,
        "total_amount": Decimal(scooter.scooter_model.last_price) + Decimal('5000.00'),
        "taxable_amount": (Decimal(scooter.scooter_model.last_price) + Decimal('5000.00')) * Decimal('0.85'),
        "gst_number": f"22AAAAA000{i}A1Z5",
        "financer": random.choice(["Bajaj Finserv", "HDFC", "Cash"]),
        "aadhar_number": f"{random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)}",
        "pan_number": f"ABCDE{random.randint(1000,9999)}F"
    })
    
    if created:
        SaleBattery.objects.create(sale_record=sale, battery=battery1)
        SaleBattery.objects.create(sale_record=sale, battery=battery2)
        
        scooter.status = 'SOLD'
        scooter.save()
        charger.status = 'SOLD'
        charger.save()
        battery1.status = 'SOLD'
        battery1.save()
        battery2.status = 'SOLD'
        battery2.save()

# Leads
for i in range(5):
    lead, _ = Lead.objects.get_or_create(customer_name=f"Lead Customer {i}", contact=f"88888888{i}8", defaults={
        "salesperson": random.choice(sales_ids),
        "interested_items": "Looking for EcoBolt 100",
        "status": "NEW",
        "aadhar_number": f"{random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)}",
        "pan_number": f"FGHIJ{random.randint(1000,9999)}K"
    })
    Quote.objects.get_or_create(lead=lead, defaults={
        "scooter_model": models_list[0],
        "quoted_price": 63000.00,
        "item_details": "Included fast charger",
        "valid_until": timezone.now().date() + timedelta(days=7)
    })

print("Dummy data successfully generated!")
