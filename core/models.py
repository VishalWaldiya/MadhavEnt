from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
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

    def __str__(self):
        return f"{self.username} ({self.role})"

class Note(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
