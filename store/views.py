from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction
from django.conf import settings
from django_zarinpal.services import start_transaction, verify_transaction
from django.contrib import messages
import requests
from .forms import CouponApplyForm
from decimal import Decimal
from django.utils import timezone
from .services import get_shipping_cost

from .models import GoldItem, Order, CartItem, OrderItem, GoldPrice, Coupon, ShippingSettings
# Create your views here.


class HomeView(TemplateView):
    template_name = "store/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_items"] = GoldItem.objects.filter(stock__gt=0).order_by(
            "-created_at"
        )[:8]
        context["latest_gold_price"] = GoldPrice.objects.first()
        return context


class GoldItemListView(ListView):
    model = GoldItem
    template_name = "store/golditem_list.html"
    context_object_name = "items"
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = super().get_queryset()

        min_price = self.request.GET.get("min_price")
        max_price = self.request.GET.get("max_price")
        category = self.request.GET.get("category")
        
        if category:
            qs = qs.filter(category=category)

        if min_price:
            qs = qs.filter(final_price__gte=min_price)
        if max_price:
            qs = qs.filter(final_price__lte=max_price)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["min_price"] = self.request.GET.get("min_price", "")
        context["max_price"] = self.request.GET.get("max_price", "")
        context["current_category"] = self.request.GET.get("category", "")  # NEW
        context["categories"] = GoldItem.Category.choices                   # NEW
        context["latest_gold_price"] = GoldPrice.objects.first()
        return context


class GoldItemDetailView(DetailView):
    model = GoldItem
    template_name = "store/golditem_detail.html"
    context_object_name = "item"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["latest_gold_price"] = GoldPrice.objects.first()
        return context


class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    template_name = "store/order_form.html"
    fields = ["quantity", "full_name", "phone", "address_line"]


    def dispatch(self, request, *args, **kwargs):
        self.item = get_object_or_404(GoldItem, pk=kwargs["item_id"])
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        quantity = form.cleaned_data["quantity"]
        if quantity > self.item.stock:
            return render(
                self.request,
                self.template_name,
                {
                    "form": form,
                    "item": self.item,
                    "error": "Not enough stock available.",
                },
            )
        form.instance.user = self.request.user
        form.instance.item = self.item

        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["item"] = self.item
        return context
    
    def get_success_url(self):
        return reverse_lazy("store:golditem_detail", kwargs={"pk" : self.item.pk})
    

class MyOrdersListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "store/my_orders.html"
    context_object_name = "orders"
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related("orderitems__item")
            .order_by("-created_at")
        )


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "store/order_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "orderitems__item"
        )
    

@method_decorator(login_required, name="dispatch")
class CartAddView(View):
    def post(self, request, item_id):
        item = get_object_or_404(GoldItem, pk=item_id)
        quantity = int(request.POST.get("quantity", 1))

        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            item=item,
            defaults={"quantity": quantity},
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return redirect("store:cart_detail")

@login_required
def remove_from_cart(request, item_id):

    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    if request.method == "POST":
        print("DELETING:", cart_item.id)
        cart_item.delete()
    return redirect("store:cart_detail")

@method_decorator(login_required, name="dispatch")
class CartDetailView(View):
    def get(self, request):
        cart_items = CartItem.objects.filter(user=request.user)
        rows = []
        total = 0

        for ci in cart_items:
            line_total = ci.item.final_price * ci.quantity
            total += line_total
            rows.append(
                {
                    "id": ci.id,
                    "item": ci.item,
                    "quantity": ci.quantity,
                    "line_total": line_total,
                }
            )

        return render(
            request,
            "store/cart_detail.html",
            {"rows": rows, "total": total},
        )
    


class CheckoutView(LoginRequiredMixin, View):
    template_name = "store/checkout.html"

    def get(self, request):
        cart_items = CartItem.objects.filter(user=request.user)

        if not cart_items:
            return redirect("store:cart_detail")
        
        total = sum(ci.item.final_price * ci.quantity for ci in cart_items)
        # coupon from session
        coupon_code = request.session.get("coupon_code")
        coupon = None
        discount = Decimal("0")
        coupon_message = None

        if coupon_code:
            now = timezone.now()
            try:
                coupon = Coupon.objects.get(
                    code__iexact=coupon_code,
                    active=True,
                    valid_from__lte=now,
                    valid_to__gte=now,
                )
                discount = coupon.get_discount_value(total)
            except Coupon.DoesNotExist:
                request.session.pop("coupon_code", None)
                coupon_message = "کد تخفیف ذخیره‌شده دیگر معتبر نیست."

        items_total = total - discount
        shipping_cost = get_shipping_cost(items_total)
        payable = items_total + shipping_cost

        return render(
            request,
            self.template_name,
            {
                "cart_items": cart_items,
                "total": total,              # total of items
                "discount": discount,
                "items_total": items_total,  # after discount, before shipping
                "shipping_cost": shipping_cost,
                "payable": payable,          # final amount
                "coupon_form": CouponApplyForm(
                    initial={"code": coupon_code} if coupon_code else None
                ),
                "applied_coupon": coupon,
                "coupon_message": coupon_message,
            },
        )
    
    @transaction.atomic
    def post(self, request):
        action = request.POST.get("action")
        cart_items = CartItem.objects.select_for_update().filter(user=request.user)
        if not cart_items.exists():
            return redirect("store:cart_detail")
        
        total = sum(x.item.final_price * x.quantity for x in cart_items)
        
        # 1) If user clicked "apply coupon", just validate and re-render page
        if action == "apply_coupon":
            form = CouponApplyForm(request.POST)
            discount = Decimal("0")
            coupon = None
            message = None

            if form.is_valid():
                code = form.cleaned_data["code"]
                if not code:
                    # user cleared the field: remove coupon from session
                    request.session.pop("coupon_code", None)
                    coupon = None
                    discount = Decimal("0")
                    message = "کد تخفیف حذف شد."
                now = timezone.now()
                try:
                    coupon = Coupon.objects.get(
                        code__iexact=code,
                        active=True,
                        valid_from__lte=now,
                        valid_to__gte=now,
                    )
                    discount = coupon.get_discount_value(total)
                    request.session["coupon_code"] = coupon.code
                except Coupon.DoesNotExist:
                    # clear from session and form
                    request.session.pop("coupon_code", None)
                    form = CouponApplyForm()  # empty form, no code
                    message = "کد تخفیف نامعتبر است یا منقضی شده است."

                items_total = total - discount
                shipping_cost = get_shipping_cost(items_total)
                payable = items_total + shipping_cost

            return render(
                request,
                self.template_name,
                {
                    "cart_items": cart_items,
                    "total": total,
                    "discount": discount,
                    "items_total": items_total,
                    "shipping_cost": shipping_cost,
                    "payable": payable,
                    "coupon_form": form,
                    "applied_coupon": coupon,
                    "coupon_message": message,
                },
            )
        
        full_name = request.POST.get("full_name")
        phone = request.POST.get("phone")
        address_line = request.POST.get("address_line")

        for ci in cart_items:
            if ci.quantity > ci.item.stock:
                return render(
                    request,
                    self.template_name,
                    {
                        "cart_items": cart_items,
                        "total": total,
                        "error": f"موجودی کافی برای {ci.item.name} نیست.",
                        "coupon_form": CouponApplyForm(),
                    },
                )

        # read coupon from session again for safety
        coupon_code = request.session.get("coupon_code")
        coupon = None
        discount = Decimal("0")
        if coupon_code:
            now = timezone.now()
            try:
                coupon = Coupon.objects.get(
                    code__iexact=coupon_code,
                    active=True,
                    valid_from__lte=now,
                    valid_to__gte=now,
                )
                discount = coupon.get_discount_value(total)
            except Coupon.DoesNotExist:
                request.session.pop("coupon_code", None)

        items_total = total - discount
        shipping_cost = get_shipping_cost(items_total)
        payable = items_total + shipping_cost
    
            
        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            address_line=address_line,
            status="PENDING",
            coupon=coupon if hasattr(Order, "coupon") else None,
            discount_amount=discount if hasattr(Order, "discount_amount") else None,
            total_amount=payable if hasattr(Order, "total_amount") else None,
            shipping_cost=shipping_cost if hasattr(Order, "shipping_cost") else None,
        )
        
        
                
        request_data = {
            "merchant_id": settings.ZARINPAL_MERCHANT_ID,
            "amount": int(payable),  # Zarinpal expects integer
            "callback_url": settings.ZARINPAL_CALLBACK_URL,
            "description": f"پرداخت سفارش #{order.id}",
            "metadata": {
                "mobile": phone,
                "email": request.user.email,
                "order_id": str(order.id),
            },
        }
        print(payable)

        response = requests.post(
            settings.ZARINPAL_REQUEST_URL,
            json=request_data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        data = response.json()
        print(data)

        if data.get("data") and data["data"].get("code") == 100:
            authority = data["data"]["authority"]
            order.zarinpal_authority = authority
            order.save()
            # redirect to StartPay like docs
            return redirect(settings.ZARINPAL_STARTPAY_URL + authority)
        else:
            error_message = "خطا در اتصال به درگاه پرداخت."
            return render(
                request,
                self.template_name,
                {
                    "cart_items": cart_items,
                    "total": total,
                    "error": error_message,
                },
            )
        # for ci in cart_items:
        #     OrderItem.objects.create(
        #         order=order,
        #         item=ci.item,
        #         quantity=ci.quantity,
        #         price_at_purchase=ci.item.final_price,
        #     )
        #     ci.item.stock -= ci.quantity
        #     ci.item.save()

        # cart_items.delete()

        return redirect("store:my_orders")    

class ZarinpalCallbackView(LoginRequiredMixin, View):
    def get(self, request):
        status = request.GET.get("Status")
        authority = request.GET.get("Authority")

        if status != "OK" or not authority:
            messages.error(request, "پرداخت ناموفق بود یا لغو شد.")
            return redirect("store:my_orders")

        order = get_object_or_404(
            Order,
            zarinpal_authority=authority,
            user=request.user,
        )

        verify_data = {
            "merchant_id": settings.ZARINPAL_MERCHANT_ID,
            "amount": int(order.total_amount),  # you may need a property/field for total
            "authority": authority,
        }

        response = requests.post(
            settings.ZARINPAL_VERIFY_URL,
            json=verify_data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        data = response.json()

        if data.get("data") and data["data"].get("code") in (100, 101):
            # success: finalize order
            cart_items = CartItem.objects.filter(user=request.user)
            for ci in cart_items:
                ci.item.stock -= ci.quantity
                ci.item.save()
            cart_items.delete()

            order.status = "PAID"
            order.save()

            ref_id = data["data"].get("ref_id")
            messages.success(request, f"پرداخت موفق بود. کد پیگیری: {ref_id}")
        else:
            order.status = "PAYMENT_FAILED"
            order.save()
            messages.error(request, "تأیید پرداخت ناموفق بود.")

        return redirect("store:my_orders")

def parsian_coin_security(request):
    return render(request, "store/parsian_coin_security.html")