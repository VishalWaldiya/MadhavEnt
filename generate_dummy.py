import os
import django
import random
from decimal import Decimal
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from inventory.models import ScooterModel, Scooter, Battery, Charger, SparePart
from sales.models import (
    SaleRecord, SaleScooterItem, SaleBatteryItem,
    SaleChargerItem, SaleSparePartItem
)
from leads.models import Lead, Quote, QuoteItem

User = get_user_model()

print("Seeding rich EV Stock Manager data...")

# 1. Admin & Sales Users
admin, created = User.objects.get_or_create(username='admin', defaults={
    'first_name': 'Vishal',
    'last_name': 'Waldiya',
    'role': 'ADMIN',
    'email': 'admin@evstock.local'
})
admin.set_password('admin')
admin.role = 'ADMIN'
admin.is_staff = True
admin.is_superuser = True
admin.save()

sales_users = []
for i in range(1, 4):
    u, c = User.objects.get_or_create(username=f'sales{i}', defaults={
        'first_name': f'Salesperson',
        'last_name': f'{i}',
        'role': 'SALES'
    })
    if c:
        u.set_password('sales123')
        u.save()
    sales_users.append(u)

# 2. Scooter Models with Battery Configuration Dependent Ranges
scooter_models_data = [
    {
        "name": "EcoBolt 100",
        "watts": 1200,
        "charging_time": 4.0,
        "cost_price": Decimal("48000.00"),
        "selling_price": Decimal("64999.00"),
        "default_range_km": 80,
        "battery_lithium_60w_range": 85,
        "battery_lithium_72w_range": 110,
        "battery_lead_60w_range": 55,
        "battery_lead_72w_range": 70,
        "description": "City commuter scooter engineered for daily urban trips."
    },
    {
        "name": "VoltMax Pro",
        "watts": 2500,
        "charging_time": 5.5,
        "cost_price": Decimal("68000.00"),
        "selling_price": Decimal("94999.00"),
        "default_range_km": 115,
        "battery_lithium_60w_range": 105,
        "battery_lithium_72w_range": 140,
        "battery_lead_60w_range": 70,
        "battery_lead_72w_range": 90,
        "description": "High-performance long range scooter with regenerative braking."
    },
    {
        "name": "CityGlide E",
        "watts": 800,
        "charging_time": 3.0,
        "cost_price": Decimal("32000.00"),
        "selling_price": Decimal("44999.00"),
        "default_range_km": 60,
        "battery_lithium_60w_range": 65,
        "battery_lithium_72w_range": 80,
        "battery_lead_60w_range": 45,
        "battery_lead_72w_range": 55,
        "description": "Lightweight economical electric scooter for short commutes."
    },
]

created_models = []
for data in scooter_models_data:
    sm, _ = ScooterModel.objects.get_or_create(name=data["name"], defaults=data)
    created_models.append(sm)

# 3. Physical Scooter Inventory Units
colors = ["Matte Black", "Metallic Pearl White", "Ocean Blue", "Ruby Red", "Slate Gray"]
for model in created_models:
    for i in range(1, 8):
        chassis = f"CH-{model.name[:3].upper()}-{1000 + i * 17}"
        Scooter.objects.get_or_create(
            chassis_number=chassis,
            defaults={
                "scooter_model": model,
                "motor_number": f"MOT-{2000 + i * 29}",
                "color": colors[i % len(colors)],
                "cost_price": model.cost_price,
                "selling_price": model.selling_price,
                "status": "AVAILABLE",
                "supplier_details": "Direct OEM Factory Dispatch"
            }
        )

# 4. Battery Inventory (with separate With Scooter vs Without Scooter pricing)
batteries_data = [
    {
        "name": "Lithium Pro 60V 30Ah",
        "type": "LITHIUM",
        "voltage": "60V",
        "capacity_ah": "30Ah",
        "cost_price": Decimal("16500.00"),
        "with_scooter": Decimal("21000.00"),
        "without_scooter": Decimal("26000.00"),
        "count": 15,
        "prefix": "BAT-L60"
    },
    {
        "name": "Lithium Ultra 72V 34Ah",
        "type": "LITHIUM",
        "voltage": "72V",
        "capacity_ah": "34Ah",
        "cost_price": Decimal("22000.00"),
        "with_scooter": Decimal("28000.00"),
        "without_scooter": Decimal("34000.00"),
        "count": 15,
        "prefix": "BAT-L72"
    },
    {
        "name": "HeavyDuty Lead Acid 60V 28Ah",
        "type": "LEAD_ACID",
        "voltage": "60V",
        "capacity_ah": "28Ah",
        "cost_price": Decimal("9000.00"),
        "with_scooter": Decimal("12500.00"),
        "without_scooter": Decimal("16000.00"),
        "count": 10,
        "prefix": "BAT-LA60"
    },
    {
        "name": "HeavyDuty Lead Acid 72V 30Ah",
        "type": "LEAD_ACID",
        "voltage": "72V",
        "capacity_ah": "30Ah",
        "cost_price": Decimal("11000.00"),
        "with_scooter": Decimal("14500.00"),
        "without_scooter": Decimal("18500.00"),
        "count": 10,
        "prefix": "BAT-LA72"
    },
]

for bdata in batteries_data:
    for i in range(1, bdata["count"] + 1):
        serial = f"{bdata['prefix']}-{100 + i}"
        Battery.objects.get_or_create(
            serial_number=serial,
            defaults={
                "name": bdata["name"],
                "battery_type": bdata["type"],
                "voltage": bdata["voltage"],
                "capacity_ah": bdata["capacity_ah"],
                "cost_price": bdata["cost_price"],
                "price_with_scooter": bdata["with_scooter"],
                "price_without_scooter": bdata["without_scooter"],
                "status": "AVAILABLE"
            }
        )

# 5. Charger Inventory (1st Charger bundled with scooter is free ₹0.00, Standalone is priced)
chargers_data = [
    {
        "name": "Fast Charger 60V 5A Smart",
        "type": "Standard Fast Charger",
        "voltage": "60V",
        "cost_price": Decimal("1400.00"),
        "with_scooter": Decimal("0.00"),  # Free 1st charger with scooter!
        "without_scooter": Decimal("2499.00"),
        "count": 15,
        "prefix": "CHG-60V"
    },
    {
        "name": "Rapid Smart Charger 72V 6A",
        "type": "Rapid Smart Charger",
        "voltage": "72V",
        "cost_price": Decimal("1900.00"),
        "with_scooter": Decimal("0.00"),
        "without_scooter": Decimal("3299.00"),
        "count": 15,
        "prefix": "CHG-72V"
    },
]

for cdata in chargers_data:
    for i in range(1, cdata["count"] + 1):
        serial = f"{cdata['prefix']}-{200 + i}"
        Charger.objects.get_or_create(
            serial_number=serial,
            defaults={
                "name": cdata["name"],
                "charger_type": cdata["type"],
                "voltage": cdata["voltage"],
                "cost_price": cdata["cost_price"],
                "price_with_scooter": cdata["with_scooter"],
                "price_without_scooter": cdata["without_scooter"],
                "status": "AVAILABLE"
            }
        )

# 6. Spare Parts Inventory
spare_parts_data = [
    {"name": "Front Disc Brake Pad Set", "part_number": "SP-BRK-01", "category": "Braking", "qty": 20, "cost": Decimal("220.00"), "price": Decimal("499.00")},
    {"name": "Tubeless Tyre 90/90-12", "part_number": "SP-TYR-02", "category": "Wheels & Tyres", "qty": 14, "cost": Decimal("750.00"), "price": Decimal("1450.00")},
    {"name": "LED Projector Headlight Unit", "part_number": "SP-LGT-03", "category": "Electrical", "qty": 8, "cost": Decimal("850.00"), "price": Decimal("1800.00")},
    {"name": "Aerodynamic Rear View Mirrors (Pair)", "part_number": "SP-MIR-04", "category": "Body", "qty": 25, "cost": Decimal("180.00"), "price": Decimal("450.00")},
    {"name": "All-Weather Heavy Duty Floor Mat", "part_number": "SP-MAT-05", "category": "Accessories", "qty": 30, "cost": Decimal("150.00"), "price": Decimal("399.00")},
    {"name": "Smart Bluetooth Throttle Controller", "part_number": "SP-THR-06", "category": "Electronics", "qty": 5, "cost": Decimal("1200.00"), "price": Decimal("2499.00")},
]

for sp in spare_parts_data:
    SparePart.objects.get_or_create(
        part_number=sp["part_number"],
        defaults={
            "name": sp["name"],
            "category": sp["category"],
            "quantity": sp["qty"],
            "cost_price": sp["cost"],
            "selling_price": sp["price"],
            "status": "AVAILABLE"
        }
    )

# 7. Record realistic demo sales with multi-category bundles and discounts!
customers_info = [
    {"name": "Rajesh Sharma", "phone": "9823011223", "aadhar": "4521 8892 1032", "pan": "ABCDE1234F"},
    {"name": "Ananya Desai", "phone": "9876543210", "aadhar": "7812 3456 9012", "pan": "FGHIJ5678K"},
    {"name": "Karan Malhotra", "phone": "9911223344", "aadhar": "9021 6543 2109", "pan": "LMNOP9012Q"},
]

for i, cust in enumerate(customers_info):
    c_user, _ = User.objects.get_or_create(
        phone_number=cust["phone"],
        defaults={
            "first_name": cust["name"].split()[0],
            "last_name": cust["name"].split()[1],
            "role": "CUSTOMER",
            "username": f"cust_{cust['phone']}",
            "aadhar_number": cust["aadhar"],
            "pan_number": cust["pan"]
        }
    )

    avail_scooter = Scooter.objects.filter(status='AVAILABLE').first()
    avail_bat_with = Battery.objects.filter(status='AVAILABLE', voltage=avail_scooter.scooter_model.watts and '60V').first()
    avail_bat_without = Battery.objects.filter(status='AVAILABLE').exclude(id=getattr(avail_bat_with, 'id', None)).first()
    avail_chg = Charger.objects.filter(status='AVAILABLE').first()
    avail_spare = SparePart.objects.filter(status='AVAILABLE').first()

    if not avail_scooter:
        break

    # Calculate itemized amounts
    scooter_price = avail_scooter.scooter_model.selling_price
    bat_with_price = avail_bat_with.price_with_scooter if avail_bat_with else Decimal('21000.00')
    bat_without_price = avail_bat_without.price_without_scooter if avail_bat_without else Decimal('26000.00')
    chg_price = Decimal('0.00') # 1st Charger with scooter is Free!
    spare_price = avail_spare.selling_price if avail_spare else Decimal('450.00')

    subtotal = scooter_price + bat_with_price + (bat_without_price * 2) + chg_price + spare_price
    
    # 10% Diwali / Festive Discount
    discount_pct = Decimal('10.00')
    discount_amt = (subtotal * discount_pct / Decimal('100.00')).quantize(Decimal('0.01'))
    total_bill = subtotal - discount_amt
    taxable = (total_bill * Decimal('0.82')).quantize(Decimal('0.01'))

    sale = SaleRecord.objects.create(
        customer=c_user,
        salesperson=sales_users[i % len(sales_users)],
        financer="Bajaj Finserv EMI" if i == 0 else "HDFC Consumer Finance" if i == 1 else "Direct Cash",
        gst_number=f"07AABCU9603R1Z{i}",
        subtotal_amount=subtotal,
        discount_percentage=discount_pct,
        discount_amount=discount_amt,
        discount_reason="Diwali Festive Discount" if i == 0 else "Family and Friends Discount" if i == 1 else "Season End Clearance",
        taxable_amount=taxable,
        total_amount=total_bill
    )

    # Add Scooter line item with dynamic battery range
    configured_range = avail_scooter.scooter_model.get_range_for_battery(avail_bat_with)
    SaleScooterItem.objects.create(
        sale_record=sale,
        scooter_model=avail_scooter.scooter_model,
        scooter=avail_scooter,
        chassis_number=avail_scooter.chassis_number,
        motor_number=avail_scooter.motor_number,
        color=avail_scooter.color,
        unit_price=scooter_price,
        configured_battery=avail_bat_with,
        configured_range_km=configured_range
    )
    avail_scooter.status = 'SOLD'
    avail_scooter.save()

    # Add Bundled Battery (With Scooter)
    if avail_bat_with:
        SaleBatteryItem.objects.create(
            sale_record=sale,
            battery=avail_bat_with,
            battery_name=avail_bat_with.name,
            serial_number=avail_bat_with.serial_number,
            sale_category='WITH_SCOOTER',
            quantity=1,
            unit_price=bat_with_price,
            total_price=bat_with_price
        )
        avail_bat_with.status = 'SOLD'
        avail_bat_with.save()

    # Add Standalone Extra Batteries (Without Scooter)
    if avail_bat_without:
        SaleBatteryItem.objects.create(
            sale_record=sale,
            battery=avail_bat_without,
            battery_name=avail_bat_without.name,
            serial_number=avail_bat_without.serial_number,
            sale_category='WITHOUT_SCOOTER',
            quantity=2,
            unit_price=bat_without_price,
            total_price=bat_without_price * 2
        )
        avail_bat_without.status = 'SOLD'
        avail_bat_without.save()

    # Add Charger (Bundled 1st Charger at ₹0.00 Free)
    if avail_chg:
        SaleChargerItem.objects.create(
            sale_record=sale,
            charger=avail_chg,
            charger_name=avail_chg.name,
            serial_number=avail_chg.serial_number,
            sale_category='WITH_SCOOTER',
            quantity=1,
            unit_price=Decimal('0.00'),
            total_price=Decimal('0.00')
        )
        avail_chg.status = 'SOLD'
        avail_chg.save()

    # Add Spare Part
    if avail_spare:
        SaleSparePartItem.objects.create(
            sale_record=sale,
            spare_part=avail_spare,
            part_name=avail_spare.name,
            part_number=avail_spare.part_number,
            quantity=1,
            unit_price=spare_price,
            total_price=spare_price
        )
        avail_spare.quantity -= 1
        avail_spare.save()

# 8. Create Demo Leads and Quotes
lead_cust, _ = User.objects.get_or_create(
    phone_number="9811223344",
    defaults={
        "first_name": "Siddharth",
        "last_name": "Verma",
        "role": "CUSTOMER",
        "username": "cust_siddharth"
    }
)
demo_lead, _ = Lead.objects.get_or_create(
    customer=lead_cust,
    defaults={
        "salesperson": sales_users[0],
        "interested_items": "Inquiring about VoltMax Pro with extra 72V Lithium battery pack.",
        "status": "IN_PROGRESS"
    }
)

q_subtotal = Decimal("124999.00")
q_disc_pct = Decimal("5.00")
q_disc_amt = Decimal("6249.95")
q_quoted = q_subtotal - q_disc_amt

quote, _ = Quote.objects.get_or_create(
    lead=demo_lead,
    defaults={
        "subtotal_amount": q_subtotal,
        "discount_percentage": q_disc_pct,
        "discount_amount": q_disc_amt,
        "discount_reason": "First-time Buyer Welcome Discount",
        "quoted_price": q_quoted,
        "valid_until": timezone.now().date() + timedelta(days=14),
        "item_details": "Includes 1x Free Smart Charger 72V + Free Floor Mat"
    }
)

QuoteItem.objects.get_or_create(
    quote=quote,
    item_name="VoltMax Pro Scooter",
    defaults={"item_type": "SCOOTER", "quantity": 1, "unit_price": Decimal("94999.00"), "total_price": Decimal("94999.00")}
)
QuoteItem.objects.get_or_create(
    quote=quote,
    item_name="Lithium Ultra 72V 34Ah (Bundled)",
    defaults={"item_type": "BATTERY", "sale_category": "WITH_SCOOTER", "quantity": 1, "unit_price": Decimal("28000.00"), "total_price": Decimal("28000.00")}
)
QuoteItem.objects.get_or_create(
    quote=quote,
    item_name="Rapid Smart Charger 72V 6A (Included)",
    defaults={"item_type": "CHARGER", "sale_category": "WITH_SCOOTER", "quantity": 1, "unit_price": Decimal("0.00"), "total_price": Decimal("0.00")}
)
QuoteItem.objects.get_or_create(
    quote=quote,
    item_name="All-Weather Floor Mat",
    defaults={"item_type": "SPARE", "quantity": 1, "unit_price": Decimal("0.00"), "total_price": Decimal("0.00")}
)

print("Rich dummy data generated successfully!")
