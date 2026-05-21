from .models import CartItem, Announcement


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

def current_announcement(request):
    ann = Announcement.objects.filter(is_active=True).order_by("-created_at").first()
    return {"current_announcement": ann}