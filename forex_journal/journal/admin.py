from django.contrib import admin
from .models import Journal, Strategy, Indicator, Session, Day, PhotoAttachment, BeforeTradeData, StrategyDoc, \
    StartingDetails, Asset, PredefinedAssets, TradingSector


class JournalAdmin(admin.ModelAdmin):
    list_display = ("id", "pair", "win_loss", "buy_sell", "time_frame",
                    "day", "entry_time", "entry_price", "exit_time",
                    "exit_price", "profit", "tp_price", "sl_price", "session",
                    "position_size", "strategy", "r_r", "created_at")
    ordering = ('created_at',)
    search_fields = ["pair"]


admin.site.register(Journal, JournalAdmin)


class IndicatorAdmin(admin.ModelAdmin):
    list_display = ("indicator",)


admin.site.register(Indicator, IndicatorAdmin)


class StrategyAdmin(admin.ModelAdmin):
    list_display = ("title", "performance", "losing_trades", "winning_trades")  # "indicators")


admin.site.register(Strategy, StrategyAdmin)

admin.site.register(Day)

admin.site.register(PhotoAttachment)

admin.site.register(Session)

admin.site.register(BeforeTradeData)

admin.site.register(StrategyDoc)

admin.site.register(Asset)

admin.site.register(StartingDetails)

admin.site.register(PredefinedAssets)

admin.site.register(TradingSector)
