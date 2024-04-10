from django.contrib import admin
from django.urls import path
from . import views
from .views import *
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

app_name = "trade_debug"
urlpatterns = [path("trade_debug/", TradeDebugView.as_view(), name="trade_debug"),
               path("search_debug/", search_debug, name="search_debug")
               ]
