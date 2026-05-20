from .models import CartItem


def cart(request):
    if request.user.is_authenticated:
        count = (
            CartItem.objects.filter(user=request.user)
            .values_list("quantity", flat=True)
        )
        total_qty = sum(count) if count else 0
    else:
        total_qty = 0
    return {"cart_item_count": total_qty}
