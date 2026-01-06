from django.db import models
from django.conf import settings


class Product(models.Model):
    """Model for beauty clinic products"""
    product_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    product_image = models.ImageField(upload_to='products/', blank=True, null=True)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name

    class Meta:
        db_table = 'products'
        ordering = ['product_name']


class ProductImage(models.Model):
    """Model for additional product images"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/images/')
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.product_name} - Image {self.id}"

    class Meta:
        db_table = 'product_images'
        ordering = ['-is_primary', '-created_at']


class StockHistory(models.Model):
    """Model to track all stock changes (add/minus) for inventory management"""
    ACTION_CHOICES = [
        ('add', 'Stock Added'),
        ('minus', 'Stock Reduced'),
        ('order', 'Customer Order'),
        ('return', 'Stock Returned'),
        ('adjustment', 'Manual Adjustment'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_history')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    quantity = models.IntegerField(help_text="Positive for additions, negative for reductions")
    previous_stock = models.IntegerField(help_text="Stock level before this change")
    new_stock = models.IntegerField(help_text="Stock level after this change")
    reason = models.TextField(blank=True, null=True, help_text="Reason for stock change")
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_changes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product.product_name} - {self.action} ({self.quantity}) on {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        db_table = 'stock_history'
        ordering = ['-created_at']
        verbose_name = 'Stock History'
        verbose_name_plural = 'Stock History'