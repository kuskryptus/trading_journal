import logging

from accounts.forms import CustomUserCreationForm, OnboardingForm
from accounts.models import CustomUser
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from django.shortcuts import HttpResponseRedirect, redirect, render
from django.urls import reverse
from journal.models import StartingDetails, TradingSector

from .models import CustomUser

log = logging.getLogger("journal")


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.instance.timezone = request.POST.get('userTimezone')
            form.save()
            return redirect("/accounts/login/")
    else:
        form = CustomUserCreationForm()

    return render(request, "accounts/registration.html", {"form": form})


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"

    def form_valid(self, form):
        user = form.get_user()
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        user = authenticate(username=username, password=password)
        if user is not None:
            login(self.request, user)
            if user.onboarded:
                return redirect("journal:home")
            else:
                return redirect("accounts:onboard")
        else:
            return super().form_invalid(form)


def logout(request):
    django_logout(request)
    return HttpResponseRedirect(reverse("accounts:login"))


def show_settings(request):
    return render(request, "settings.html")


def is_user_in_group(username, group_name):
    try:
        user = CustomUser.objects.get(username=username)
        return user.groups.filter(name=group_name).exists()
    except CustomUser.DoesNotExist:
        return False


def is_user_in_group_by_email(email, group_name):
    try:
        user = CustomUser.objects.get(email=email)
        return user.groups.filter(name=group_name).exists()
    except CustomUser.DoesNotExist:
        return False


def check_user_status(request):
    user1 = is_user_in_group("eror7", "Administrators")
    user2 = is_user_in_group("eror7", "Users")

    print(user1, user2)
    return HttpResponse(user1, user2)


def onboarding(request):
    if request.method == "POST":
        try:
            form = OnbordingForm(request.POST)

            if form.is_valid():
                print("Form data:", form.cleaned_data)
                isinstance = form.save(commit=False)

                isinstance.user = request.user
                request.user.onboarded = True
                request.user.save()
                isinstance.save()
                return redirect("accounts:onboard_next")
        except Exception as e:
            print("Error:", e)

    else:
        form = OnbordingForm()
    return render(request, "accounts/onboard.html", {"form": form})


def onboarding_1(request):
    sectors = TradingSector.objects.all()

    if request.method == "POST":
        try:
            selected_sectors_ids = request.POST.getlist('selected_sectors')
            selected_sectors = [int(id) for id in selected_sectors_ids if id.isdigit()]
            starting_details, created = StartingDetails.objects.get_or_create(user=request.user)
            starting_details.selected_sectors.clear()
            starting_details.selected_sectors.add(*selected_sectors)

            return redirect("journal:home")

        except Exception as e:
            log.exception("Error", e)

    return render(request, "accounts/onboard_1.html", {"sectors": sectors})
