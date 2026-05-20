# products/models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone  # Add this import


# =========================
# CATEGORY
# =========================
# products/models.py - Category model without slug

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

# =========================
# SUB CATEGORY
# =========================
class SubCategory(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="subcategories"
    )

    def __str__(self):
        return f"{self.category.name} - {self.name}"


# =========================
# PRODUCT
# =========================
class Product(models.Model):
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=255, default='Premium')

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    sub_category = models.ForeignKey(
        SubCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    description = models.TextField()

    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    size = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=100, blank=True, null=True)

    image = models.ImageField(
        upload_to='products/',
        null=True,
        blank=True
    )

    is_featured = models.BooleanField(default=False)

    # UNISEX FEATURE
    gender = models.CharField(max_length=20, default="UNISEX")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # ✅ Add this field

    def delete(self, *args, **kwargs):
        """Prevent deletion if product has pending orders"""
        # Check if this product has any pending or confirmed orders
        pending_orders = self.orderitem_set.filter(
            order__status__in=['pending', 'confirmed']
        ).exists()
        
        if pending_orders:
            # Get order IDs for better error message
            order_ids = self.orderitem_set.filter(
                order__status__in=['pending', 'confirmed']
            ).values_list('order__id', flat=True)
            
            raise ValidationError(
                f"Cannot delete product '{self.name}'. "
                f"It has pending orders (Order IDs: {', '.join(map(str, order_ids))}). "
                f"Please complete or cancel these orders first."
            )
        
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.name


# =========================
# WISHLIST
# =========================
class Wishlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist_items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlisted_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'product']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"