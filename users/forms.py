from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import Profile

User = get_user_model()

INPUT_CLASS = {"class": "form-input"}


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {
            "first_name": _("First name"),
            "last_name": _("Last name"),
            "email": _("Email"),
        }
        widgets = {
            "first_name": forms.TextInput(attrs=INPUT_CLASS),
            "last_name": forms.TextInput(attrs=INPUT_CLASS),
            "email": forms.EmailInput(attrs=INPUT_CLASS),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("phone", "address")
        labels = {
            "phone": _("Phone number"),
            "address": _("Default address"),
        }
        widgets = {
            "phone": forms.TextInput(attrs={**INPUT_CLASS, "autocomplete": "tel"}),
            "address": forms.Textarea(attrs={**INPUT_CLASS, "rows": 3}),
        }
