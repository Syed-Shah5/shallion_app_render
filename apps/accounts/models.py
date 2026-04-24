from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import FileExtensionValidator

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        #email = self.normalize_email(email)
        email = self.normalize_email(email).lower()  
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'ADMIN')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('CLIENT', 'Client'),
        ('VOLUNTEER', 'Volunteer'),
        ('ADMIN', 'Admin'),
        ('STAFF', 'Staff'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Verification'),
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('INACTIVE', 'Inactive'),
    ]
    
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Verification fields
    is_email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Volunteer specific
    pvg_number = models.CharField(max_length=50, blank=True)
    pvg_verified = models.BooleanField(default=False)
    pvg_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Client specific
    gp_certificate = models.FileField(
        upload_to='gp_certificates/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    gp_certificate_verified = models.BooleanField(default=False)
    gp_certificate_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Common fields
    profile_completed = models.BooleanField(default=False)
    
    
    # System fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        app_label = 'accounts'

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()  
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.full_name} ({self.role})"