from django.contrib import messages
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView

from store.models import Order

from .forms import CustomUserCreationForm, ProfileForm, UserProfileForm
from .models import Profile

User = get_user_model()


class SignupView(CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = "registration/signup.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, _("Your account was created successfully."))
        return redirect("profile")


@method_decorator(login_required, name="dispatch")
class ProfileView(View):
    template_name = "users/profile.html"

    def _get_profile(self, user):
        profile, _ = Profile.objects.get_or_create(user=user)
        return profile

    def get(self, request):
        profile = self._get_profile(request.user)
        return render(
            request,
            self.template_name,
            self._build_context(request, profile),
        )

    def post(self, request):
        profile = self._get_profile(request.user)
        user_form = UserProfileForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, _("Profile updated successfully."))
            return redirect("profile")

        messages.error(request, _("Please fix the form errors."))
        return render(
            request,
            self.template_name,
            self._build_context(
                request,
                profile,
                user_form=user_form,
                profile_form=profile_form,
            ),
        )

    def _build_context(self, request, profile, user_form=None, profile_form=None):
        orders = Order.objects.filter(user=request.user)
        return {
            "profile": profile,
            "user_form": user_form or UserProfileForm(instance=request.user),
            "profile_form": profile_form or ProfileForm(instance=profile),
            "recent_orders": orders.order_by("-created_at")[:5],
            "order_count": orders.count(),
            "paid_count": orders.filter(status="PAID").count(),
        }
