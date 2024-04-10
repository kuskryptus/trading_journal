from django.contrib import admin
from trading_signals.models import (IndicatorMessage, ForexPair, Indicator,
                                    IndicatorValue, PriceData, TimeFrame,
                                    UserOption, PriceAlert, PriceMessage, IndicatorAlert, UserPreference)


class ForexPairAdamin(admin.ModelAdmin):
    list_display = ["id", "label", "selected"]


class ForexPairAdmin(admin.ModelAdmin):
    list_display = ["id", "pair_name", "selected"]


class AlertAdmin(admin.ModelAdmin):
    list_display = ["id", "alert_message", "created_at"]


class PriceDataAdmin(admin.ModelAdmin):
    list_display = ["id", "forex_pair", "price", "candle_close_at", "time_frame"]
    search_fields = ["forex_pair__pair_name"]


class IndicatorValueAdmin(admin.ModelAdmin):
    list_display = ["forex_pair", "indicator_type", "value", "timestamp"]


class TimeFrameAdmin(admin.ModelAdmin):
    list_display = ["time_frame_label", "selected"]


class UserOptionAdmin(admin.ModelAdmin):
    list_display = ["compare_option"]


class PriceAlertAdmin(admin.ModelAdmin):
    list_display = ["user", "forex_pair", "price_level", "actual_price", "is_active"]


class IndicatorAlertAdmin(admin.ModelAdmin):
    list_display = ["user", "pair", "user_option", "indicator", "time_frame", "created_at", "is_active"]


class PriceMessageAdmin(admin.ModelAdmin):
    list_display = ["user", "id", "alert_message", "created_at"]


class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ["user", "indicator", "time_frame", "forex_pair", "user_option"]


admin.site.register(UserPreference, UserPreferenceAdmin)
admin.site.register(PriceMessage, PriceMessageAdmin)
admin.site.register(IndicatorAlert, IndicatorAlertAdmin)
admin.site.register(PriceAlert, PriceAlertAdmin)
admin.site.register(UserOption, UserOptionAdmin)
admin.site.register(TimeFrame, TimeFrameAdmin)
admin.site.register(IndicatorValue, IndicatorValueAdmin)
admin.site.register(PriceData, PriceDataAdmin)
admin.site.register(ForexPair, ForexPairAdmin)
admin.site.register(Indicator, ForexPairAdamin)
admin.site.register(IndicatorMessage, AlertAdmin)
