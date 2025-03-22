from django.db import models
from django.contrib.auth.models import User

# Create your models here.
from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Employee(models.Model):
    ROLE_CHOICES = (
        ('Admin', 'Admin'),
        ('HR', 'HR'),
        ('Manager', 'Manager'),
        ('Employee', 'Employee'),
    )

    first_name = models.CharField(max_length=50, default="user")
    last_name = models.CharField(max_length=50, default="khan")
    email = models.EmailField(unique=True, default="default@email.com")
    password = models.CharField(max_length=255, default="defaultpassword")  # Store hashed password
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Employee')
    department = models.CharField(max_length=50, blank=True, null=True)
    date_joined = models.DateField(auto_now_add=True)

    def set_password(self, raw_password):
        """Hashes and sets the password"""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Checks password validity"""
        return check_password(raw_password, self.password)
    
    
    def check_role(self):
        return self.role

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"
