from decimal import Decimal
from .models import Coupon, ShippingSettings, GoldPrice

def get_shipping_cost(order_total):
    """
    order_total: Decimal or int (total of items BEFORE shipping)
    returns: Decimal shipping cost
    """
    total = Decimal(order_total)

    settings_qs = ShippingSettings.objects.all()
    if not settings_qs.exists():
        return Decimal("0")  # default: no shipping if not configured

    s = settings_qs.first()

    # free shipping if total >= free_from_amount
    if s.free_from_amount and total >= s.free_from_amount:
        return Decimal("0")

    return s.flat_rate or Decimal("0")