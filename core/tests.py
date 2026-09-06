from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Note
from inventory.models import StockItem, ScooterModel
from sales.models import SaleRecord
from leads.models import Lead
from tasks.models import ShopTask, TaskTemplate, TaskStage

User = get_user_model()

class SoftDeleteAndRecycleBinTests(TestCase):
    def setUp(self):
        # Create Admin and Non-Admin users
        self.admin = User.objects.create_user(
            username='admin_user',
            password='password123',
            role='ADMIN',
            is_staff=True,
            is_superuser=True
        )
        self.staff_sales = User.objects.create_user(
            username='sales_user',
            password='password123',
            role='SALES'
        )
        self.customer = User.objects.create_user(
            username='cust_user',
            password='password123',
            role='CUSTOMER',
            first_name='John',
            last_name='Doe',
            phone_number='9876543210'
        )

        self.client = Client()

    def test_admin_can_soft_delete_staff_and_customer(self):
        self.client.login(username='admin_user', password='password123')
        
        # Soft delete staff user
        response = self.client.post(reverse('delete_staff', args=[self.staff_sales.id]))
        self.assertEqual(response.status_code, 302)
        
        self.staff_sales.refresh_from_db()
        self.assertTrue(self.staff_sales.is_deleted)
        self.assertFalse(self.staff_sales.is_active)
        self.assertNotIn(self.staff_sales, User.objects.all())

        # Soft delete customer user
        response = self.client.post(reverse('delete_customer', args=[self.customer.id]))
        self.assertEqual(response.status_code, 302)
        
        self.customer.refresh_from_db()
        self.assertTrue(self.customer.is_deleted)
        self.assertNotIn(self.customer, User.objects.filter(role='CUSTOMER'))

    def test_non_admin_cannot_soft_delete_users(self):
        self.client.login(username='sales_user', password='password123')
        
        # Try to delete customer
        response = self.client.post(reverse('delete_customer', args=[self.customer.id]))
        self.assertEqual(response.status_code, 302)
        
        self.customer.refresh_from_db()
        self.assertFalse(self.customer.is_deleted)

    def test_admin_cannot_delete_self(self):
        self.client.login(username='admin_user', password='password123')
        response = self.client.post(reverse('delete_staff', args=[self.admin.id]))
        self.assertEqual(response.status_code, 302)
        
        self.admin.refresh_from_db()
        self.assertFalse(self.admin.is_deleted)

    def test_soft_deleted_user_cannot_login(self):
        self.staff_sales.soft_delete() if hasattr(self.staff_sales, 'soft_delete') else self.staff_sales.delete()
        logged_in = self.client.login(username='sales_user', password='password123')
        self.assertFalse(logged_in)

    def test_recycle_bin_view_and_permissions(self):
        # Soft delete a user and a note
        self.staff_sales.delete()
        note = Note.objects.create(title='Secret Note', content='Test Content')
        note.delete()

        # Non-admin access denied
        self.client.login(username='sales_user', password='password123')
        res = self.client.get(reverse('recycle_bin'))
        self.assertEqual(res.status_code, 302)

        # Admin access granted
        self.client.login(username='admin_user', password='password123')
        res = self.client.get(reverse('recycle_bin'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'sales_user')
        self.assertContains(res, 'Secret Note')

    def test_restore_and_hard_delete_from_recycle_bin(self):
        self.client.login(username='admin_user', password='password123')
        
        note = Note.objects.create(title='Disposable Note', content='Testing hard delete')
        note.delete()
        self.assertTrue(note.is_deleted)

        # Restore note
        res = self.client.get(reverse('restore_item', args=['note', note.id]))
        self.assertEqual(res.status_code, 302)
        note.refresh_from_db()
        self.assertFalse(note.is_deleted)

        # Soft delete again then hard delete
        note.delete()
        res = self.client.post(reverse('hard_delete_item', args=['note', note.id]))
        self.assertEqual(res.status_code, 302)
        self.assertFalse(Note.all_objects.filter(id=note.id).exists())

    def test_empty_recycle_bin(self):
        self.client.login(username='admin_user', password='password123')
        
        n1 = Note.objects.create(title='Note 1', content='...')
        n2 = Note.objects.create(title='Note 2', content='...')
        n1.delete()
        n2.delete()

        self.assertEqual(Note.all_objects.filter(is_deleted=True).count(), 2)

        res = self.client.post(reverse('empty_recycle_bin'))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Note.all_objects.filter(is_deleted=True).count(), 0)

    def test_global_search_shows_deleted_tag_and_disabled_action(self):
        self.client.login(username='admin_user', password='password123')
        
        # Create a task and soft delete it
        template = TaskTemplate.objects.create(name='Repair', prefix='REP')
        stage = TaskStage.objects.create(template=template, name='Initial Inspection')
        task = ShopTask.objects.create(template=template, task_number='REP-1', title='Motor Issue', current_stage=stage)
        task.delete()

        # Search for task
        res = self.client.get(reverse('global_search') + '?q=REP-1')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Motor Issue')
        self.assertContains(res, 'DELETED')
        self.assertContains(res, 'View Details (Disabled)')

    def test_protected_error_handling_in_empty_recycle_bin(self):
        self.client.login(username='admin_user', password='password123')
        
        scooter_model = ScooterModel.objects.create(name='Pro Model', range_km=100, watts=1000, charging_time=3.5, last_price=50000)
        stock_item = StockItem.objects.create(item_type='SCOOTER', scooter_model=scooter_model, name='Scooter 1', serial_number='SN-PROT-100')
        charger = StockItem.objects.create(item_type='CHARGER', name='Charger 1', serial_number='SN-CHG-100')
        sale = SaleRecord.objects.create(scooter_model=scooter_model, chassis_number=stock_item, motor_number='MOT-1', charger=charger, taxable_amount=100, total_amount=118)

        # Soft delete stock_item without cascading
        stock_item.delete(cascade=False)
        self.assertTrue(stock_item.is_deleted)

        res = self.client.post(reverse('empty_recycle_bin'))
        self.assertEqual(res.status_code, 302)
        
        # stock_item should still exist in database due to ProtectedError from active SaleRecord
        self.assertTrue(StockItem.all_objects.filter(id=stock_item.id).exists())

    def test_cascade_soft_delete_and_confirmation_screen(self):
        self.client.login(username='admin_user', password='password123')
        
        template = TaskTemplate.objects.create(name='Cascade Template', prefix='CAS')
        stage = TaskStage.objects.create(template=template, name='Assembly')
        task = ShopTask.objects.create(template=template, task_number='CAS-1', title='Assemble Scooter', current_stage=stage)

        # 1. Initiating delete without confirmed=1 renders confirmation screen listing connected task
        res = self.client.post(reverse('delete_template', args=[template.id]))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Confirm Soft Delete')
        self.assertContains(res, '[CAS-1] Assemble Scooter')

        # 2. Confirming delete soft-deletes both template and connected task
        res = self.client.post(reverse('delete_template', args=[template.id]), {'confirmed': '1'})
        self.assertEqual(res.status_code, 302)

        template.refresh_from_db()
        task.refresh_from_db()
        self.assertTrue(template.is_deleted)
        self.assertTrue(task.is_deleted)

        # 3. Restoring template restores connected task
        template.restore()
        template.refresh_from_db()
        task.refresh_from_db()
        self.assertFalse(template.is_deleted)
        self.assertFalse(task.is_deleted)


class PWATests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_manifest_json(self):
        res = self.client.get(reverse('manifest'))
        self.assertEqual(res.status_code, 200)
        self.assertIn('application/manifest+json', res['Content-Type'])
        self.assertContains(res, 'Shri Madhav Enterprises')
        self.assertContains(res, 'fullscreen')


    def test_service_worker(self):
        res = self.client.get(reverse('service_worker'))
        self.assertEqual(res.status_code, 200)
        self.assertIn('application/javascript', res['Content-Type'])
        self.assertEqual(res['Service-Worker-Allowed'], '/')
        self.assertContains(res, 'CACHE_NAME')

    def test_offline_view(self):
        res = self.client.get(reverse('offline'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'currently offline')

