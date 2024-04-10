from django.urls import path
from . views import *


app_name = "trading_signals"
urlpatterns = [
    path("create_signal/", save_notification_alert, name="create_signal"),
    path("trading_signals/", signal_management, name="signal_management"),
    path("remove_forex_pair/", remove_forex_pair, name="remove_forex_pair"),
    path("create_signal/save_price_alert/", save_price_alert, name="save_price_alert"),
    path("discard_indicator_alert/<int:pk>/", discard_indicator_alert, name="discard_indicator_alert"),
    path("discard_price_alert/<int:pk>", discard_price_alert, name="discard_price_alert"),
    
]
