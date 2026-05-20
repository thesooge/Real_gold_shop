from django.urls import path
from .views import (
    HomeView,
    GoldItemListView,
    GoldItemDetailView,
    OrderCreateView,
    MyOrdersListView,
    OrderDetailView,
    CartAddView,
    CartDetailView,
    CheckoutView,
    ZarinpalCallbackView,
    remove_from_cart,
)


app_name = "store"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("catalog/", GoldItemListView.as_view(), name="golditem_list"),
    path("<int:pk>/", GoldItemDetailView.as_view(), name="golditem_detail"),
    path("order/<int:item_id>/", OrderCreateView.as_view(), name="order_create"),
    path("my-orders/", MyOrdersListView.as_view(), name="my_orders"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order_detail"),
    path("cart/add/<int:item_id>/", CartAddView.as_view(), name="cart_add"),
    path("cart/remove/<int:item_id>/", remove_from_cart, name="remove_from_cart"),
    path("cart/", CartDetailView.as_view(), name="cart_detail"),
    path("cart/checkout/", CheckoutView.as_view(), name="checkout"),
    path("payment/zarinpal/callback/", ZarinpalCallbackView.as_view(), name="zarinpal_callback"),
]