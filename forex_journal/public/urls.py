from django.urls import path
from . import views

urlpatterns = [
    path("", views.lending_page, name="lending"),
]