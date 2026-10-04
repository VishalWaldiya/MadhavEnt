from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils import timezone

class SoftDeleteQuerySet(models.QuerySet):
    def delete(self, hard=False):
        if hard:
            return super().delete()
        return self.update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def restore(self):
        return self.update(is_deleted=False, deleted_at=None)

    def active(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)

class SoftDeleteManager(models.Manager):
    def __init__(self, *args, **kwargs):
        self._alive_only = kwargs.pop('alive_only', True)
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self._alive_only:
            return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)
        return SoftDeleteQuerySet(self.model, using=self._db)

    def active(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=True)

class SoftDeleteUserManager(UserManager):
    def __init__(self, *args, **kwargs):
        self._alive_only = kwargs.pop('alive_only', True)
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self._alive_only:
            return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)
        return SoftDeleteQuerySet(self.model, using=self._db)

    def active(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=True)

class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = SoftDeleteManager(alive_only=False)

    class Meta:
        abstract = True

    def get_connected_resources(self, include_deleted=False):
        return []

    def delete(self, using=None, keep_parents=False, hard=False, cascade=True):
        if hard:
            return super().delete(using=using, keep_parents=keep_parents)
        
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if hasattr(self, 'is_active'):
            self.is_active = False
        self.save(update_fields=['is_deleted', 'deleted_at'] + (['is_active'] if hasattr(self, 'is_active') else []))

        if cascade:
            for item in self.get_connected_resources(include_deleted=False):
                obj = item.get('object')
                if obj and hasattr(obj, 'delete') and not getattr(obj, 'is_deleted', False):
                    obj.delete(cascade=True)

    def restore(self, cascade=True):
        self.is_deleted = False
        self.deleted_at = None
        if hasattr(self, 'is_active'):
            self.is_active = True
        self.save(update_fields=['is_deleted', 'deleted_at'] + (['is_active'] if hasattr(self, 'is_active') else []))

        if cascade:
            for item in self.get_connected_resources(include_deleted=True):
                obj = item.get('object')
                if obj and hasattr(obj, 'restore') and getattr(obj, 'is_deleted', False):
                    obj.restore(cascade=True)


class User(AbstractUser, SoftDeleteModel):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('SALES', 'Salesperson'),
        ('CUSTOMER', 'Customer'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='SALES')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    aadhar_number = models.CharField(max_length=20, blank=True, null=True)
    pan_number = models.CharField(max_length=20, blank=True, null=True)
    aadhar_front_photo = models.ImageField(upload_to='customers/aadhar/', blank=True, null=True)
    aadhar_back_photo = models.ImageField(upload_to='customers/aadhar/', blank=True, null=True)
    pan_photo = models.ImageField(upload_to='customers/pan/', blank=True, null=True)
    misc = models.JSONField(default=dict, blank=True, null=True)

    objects = SoftDeleteUserManager()
    all_objects = SoftDeleteUserManager(alive_only=False)

    def get_connected_resources(self, include_deleted=False):
        from leads.models import Lead
        from sales.models import SaleRecord
        from tasks.models import ShopTask

        filter_func = (lambda manager: manager.all()) if include_deleted else (lambda manager: manager.filter(is_deleted=False))
        connected = []

        for lead in filter_func(Lead.all_objects.filter(models.Q(customer=self) | models.Q(salesperson=self))):
            connected.append({
                'type': 'Lead',
                'id': lead.id,
                'name': f"Lead for {lead.customer.get_full_name() if lead.customer else 'Unknown'}",
                'object': lead
            })
        for sale in filter_func(SaleRecord.all_objects.filter(customer=self)):
            scooter_title = sale.primary_scooter.name if sale.primary_scooter else "EV Bill"
            connected.append({
                'type': 'Sale Record',
                'id': sale.id,
                'name': f"Sale INV-{sale.id} ({scooter_title})",
                'object': sale
            })
        for task in filter_func(ShopTask.all_objects.filter(assigned_to=self)):
            connected.append({
                'type': 'Shop Task',
                'id': task.id,
                'name': f"Task {task.task_number}: {task.title}",
                'object': task
            })
        return connected

    def __str__(self):
        return f"{self.username} ({self.role})"


class Note(SoftDeleteModel):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class NotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preference')
    notify_on_sale = models.BooleanField(default=True)
    notify_on_task_comment = models.BooleanField(default=True)
    notify_on_broadcast = models.BooleanField(default=True)

    def __str__(self):
        return f"Notification Preference for {self.user.username}"


class PushDeviceSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.TextField(unique=True)
    p256dh = models.CharField(max_length=255, blank=True, null=True)
    auth = models.CharField(max_length=255, blank=True, null=True)
    browser_info = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Push Subscription for {self.user.username} ({self.created_at.strftime('%Y-%m-%d')})"


class BroadcastNotificationLog(models.Model):
    CATEGORY_CHOICES = (
        ('SALE', 'Sale'),
        ('TASK_COMMENT', 'Task Comment'),
        ('BROADCAST', 'Broadcast'),
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='BROADCAST')
    target_url = models.CharField(max_length=255, default='/')
    sender = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"[{self.category}] {self.title}"

