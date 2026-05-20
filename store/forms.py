from django import forms
from django.utils.translation import gettext_lazy as _


class CouponApplyForm(forms.Form):
    code = forms.CharField(
        label=_("Coupon code"),
        max_length=50,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": _("Enter coupon code"),
                "autocomplete": "off",
            }
        ),
    )