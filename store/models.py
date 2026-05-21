from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


# Create your models here.

class GoldItem(models.Model):
    name = models.CharField(max_length=200)
    class Category(models.TextChoices):
        COIN = "COIN", _("Coin")
        SHG = "SHG", _("Second-hand gold")

    category = models.CharField(
        max_length=200,
        choices=Category.choices,
    )
    base_rate_per_gram = models.PositiveIntegerField(null=True, blank=True)
    weight_gram = models.DecimalField(max_digits=10, decimal_places=3)
    profit_percent = models.PositiveIntegerField()
    final_price = models.PositiveIntegerField()
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to="gold_items/", null=True, blank=True)
    is_sellable = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.base_rate_per_gram is not None and self.profit_percent is not None:
            base_amount = Decimal(self.base_rate_per_gram) * self.weight_gram
            multiplier = Decimal("1") + (Decimal(self.profit_percent) / Decimal("100"))
            self.final_price = int(base_amount * multiplier)
        super().save(*args, **kwargs)

    @property
    def live_price(self):
        from .models import GoldPrice  # avoid circular import if needed
        latest = GoldPrice.objects.first()
        if not latest:
            return None

        # all Decimal; no floats
        base = self.weight_gram * latest.price_per_gram
        multiplier = Decimal("1") + (self.profit_percent / Decimal("100"))
        return int(base * multiplier)


    def __str__(self):
        return f"{self.name} --> {self.weight_gram}g"
    

class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", _("New")
        PAID = "PAID", _("Paid")
        PAYMENT_FAILED = "PAYMENT_FAILED", _("Payment failed")
        CANCELLED = "CANCELLED", _("Cancelled")
        SHIPPED = "SHIPPED", _("Shipped")
        PENDING = "PENDING", _("Pending payment")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.PositiveIntegerField(default=0)
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    address_line = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    zarinpal_authority = models.CharField(max_length=64, null=True, blank=True)
    coupon = models.CharField(max_length=200, null=True, blank=True)
    discount_amount = models.DecimalField(
        blank=True, null=True, max_digits=12, decimal_places=0
    )
    total_amount = models.DecimalField(
        blank=True, null=True, max_digits=12, decimal_places=0
    )
    shipping_cost = models.DecimalField(
        blank=True, null=True, max_digits=12, decimal_places=0
    )

    def __str__(self):
        return f"Order #{self.id} - {self.user}"


class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cartitems")
    item = models.ForeignKey(GoldItem, on_delete=models.CASCADE, related_name="cartitems")
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.item} {self.quantity}x" 
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="orderitems")
    item = models.ForeignKey(GoldItem, on_delete=models.CASCADE, related_name="orderitems")
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.item.name} x {self.quantity}"    
    
class GoldPrice(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    price_per_gram = models.PositiveIntegerField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.price_per_gram} at {self.created_at}"    

class Coupon(models.Model):
    PERCENT = "percent"
    AMOUNT = "amount"
    DISCOUNT_TYPE_CHOICES = [
        (PERCENT, _("Percentage")),
        (AMOUNT, _("Fixed amount")),
    ]
    code = models.CharField(max_length=20, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    discount_amount = models.PositiveIntegerField(null=True, blank=True)
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField()

    def __str__(self):
        return self.code
    
    def get_discount_value(self, total_amount):
        """
        total_amount: Decimal or int
        returns: discount to subtract from total
        """
        total = Decimal(total_amount)

        if self.discount_type == self.PERCENT and self.discount_percent:
            return total * (self.discount_percent / Decimal("100"))

        if self.discount_type == self.AMOUNT and self.discount_amount:
            # don't allow discount more than total
            return min(total, self.discount_amount)

        return Decimal("0")


class ShippingSettings(models.Model):
    flat_rate = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        help_text=_("Flat shipping fee (Toman)"),
    )
    free_from_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        help_text=_("Free shipping for orders at or above this amount (Toman)"),
    )

    class Meta:
        verbose_name = _("Shipping settings")
        verbose_name_plural = _("Shipping settings")

    def __str__(self):
        return str(_("Shipping settings"))


class Announcement(models.Model):
    message = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message[:50]        