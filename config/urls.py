"""
URL configuration for config project.
"""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.dispatch import Signal
from django.urls import include, path

from users.views import SignupView

_original_signal_init = Signal.__init__


def _compat_signal_init(self, *args, **kwargs):
    kwargs.pop("providing_args", None)
    return _original_signal_init(self, *args, **kwargs)


Signal.__init__ = _compat_signal_init
from django_zarinpal import urls as zarinpal_urls  # noqa: E402

Signal.__init__ = _original_signal_init

# URLs without language prefix (admin, payment gateway helpers)
urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("", include(zarinpal_urls)),
]

# Main site — default language (fa) has no URL prefix; English uses /en/
urlpatterns += i18n_patterns(
    path("", include("store.urls", namespace="store")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/", include("users.urls")),
    path("accounts/signup/", SignupView.as_view(), name="signup"),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
