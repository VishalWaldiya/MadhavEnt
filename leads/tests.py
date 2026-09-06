from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from inventory.models import ScooterModel, StockItem
from leads.models import Lead, LeadRequirement

User = get_user_model()

class LeadRequirementModuleTests(TestCase):
    def setUp(self):
        self.sales = User.objects.create_user(
            username='sales_tester',
            password='password123',
            role='SALES'
        )
        self.client = Client()

        self.model = ScooterModel.objects.create(
            name='EV Falcon 2000',
            range_km=90,
            watts=1500,
            charging_time=3.5,
            last_price=75000.00
        )

        self.spare_part = StockItem.objects.create(
            item_type='SPARE',
            name='High Performance Disc Brake',
            serial_number='SP-BRAKE-001',
            status='AVAILABLE'
        )

    def test_capture_lead_with_scooter_and_custom_requirements(self):
        self.client.login(username='sales_tester', password='password123')
        url = reverse('add_lead')

        payload = {
            'first_name': 'Ramesh',
            'last_name': 'Kumar',
            'phone_number': '9988776655',
            'interested_items': 'Customer interested in fast delivery',
            'req_source_type': ['SCOOTER', 'CUSTOM'],
            'req_scooter_id': [self.model.id, ''],
            'req_stock_id': ['', ''],
            'req_custom_name': ['', 'Extra Helmet'],
            'req_unit_price': ['75000.00', '1200.00'],
            'req_quantity': ['1', '2'],
            'req_add_to_inv': ['0', '1'], # Save helmet to DB inventory
        }

        res = self.client.post(url, data=payload)
        self.assertEqual(res.status_code, 302)

        lead = Lead.objects.filter(customer__phone_number='9988776655').first()
        self.assertIsNotNone(lead)

        reqs = lead.requirements.all()
        self.assertEqual(reqs.count(), 2)

        scooter_req = reqs.filter(scooter_model=self.model).first()
        self.assertIsNotNone(scooter_req)
        self.assertEqual(scooter_req.unit_price, 75000.00)
        self.assertEqual(scooter_req.quantity, 1)
        self.assertEqual(scooter_req.total_price, 75000.00)

        helmet_req = reqs.filter(stock_item__name='Extra Helmet').first()
        self.assertIsNotNone(helmet_req)
        self.assertEqual(helmet_req.unit_price, 1200.00)
        self.assertEqual(helmet_req.quantity, 2)
        self.assertEqual(helmet_req.total_price, 2400.00)

        # Check auto-created stock item in DB inventory
        created_stock = StockItem.objects.filter(name='Extra Helmet').first()
        self.assertIsNotNone(created_stock)
        self.assertEqual(created_stock.item_type, 'SPARE')
