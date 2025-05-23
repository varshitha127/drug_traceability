from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
import uuid

class User(AbstractUser):
    """Custom user model with additional fields"""
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    role = models.CharField(
        max_length=20,
        choices=[
            ('admin', 'Administrator'),
            ('manufacturer', 'Manufacturer'),
            ('distributor', 'Distributor'),
            ('pharmacy', 'Pharmacy'),
            ('consumer', 'Consumer')
        ],
        default='consumer'
    )
    blockchain_address = models.CharField(max_length=42, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

class Drug(models.Model):
    """Model for drug information"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    manufacturer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='manufactured_drugs')
    batch_number = models.CharField(max_length=50, unique=True)
    manufacturing_date = models.DateField()
    expiry_date = models.DateField()
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    description = models.TextField()
    image = models.ImageField(upload_to='products/', validators=[
        FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
        MaxValueValidator(5 * 1024 * 1024)  # 5MB limit
    ])
    blockchain_hash = models.CharField(max_length=66, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('production', 'Production'),
            ('processing', 'Processing'),
            ('logistics', 'Logistics'),
            ('sales', 'Sales'),
            ('delivered', 'Delivered')
        ],
        default='production'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('drug')
        verbose_name_plural = _('drugs')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} (Batch: {self.batch_number})"

class DrugTrace(models.Model):
    """Model for drug traceability information"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='traces')
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='drug_traces')
    action = models.CharField(
        max_length=20,
        choices=[
            ('manufactured', 'Manufactured'),
            ('processed', 'Processed'),
            ('shipped', 'Shipped'),
            ('received', 'Received'),
            ('sold', 'Sold')
        ]
    )
    location = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    blockchain_hash = models.CharField(max_length=66, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('drug trace')
        verbose_name_plural = _('drug traces')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.drug.name} - {self.action} by {self.actor.username}"
