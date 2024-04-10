from django.urls import path
from accounts.views import register
from django.contrib.auth.views import LoginView
from .forms import CustomUserCreationForm
from .views import *
from .views import onboarding

app_name = "accounts"

urlpatterns = [
    path("register/", register, name="register"),
    path("logout/", logout, name="logout"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("onboard/", onboarding, name="onboard"),
    path("onboard_next/", onboarding_1, name="onboard_next"),
]
