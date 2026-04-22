from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('SALES', 'Salesperson'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='SALES')
    misc = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.role})"
