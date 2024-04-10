from django.db import models
from django.conf import settings


class Indicator(models.Model):
    label = models.CharField(max_length=100)
    selected = models.BooleanField(default=False)

    def __str__(self):
        return self.label

    class Meta:
        app_label = 'trading_signals'


class TimeFrame(models.Model):
    time_frame_label = models.CharField(max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)
    selected = models.BooleanField(default=False)

    def __str__(self):
        return self.time_frame_label

    class Meta:
        app_label = 'trading_signals'


class ForexPair(models.Model):
    pair_name = models.CharField(max_length=10)
    selected = models.BooleanField(default=False)

    def __str__(self):
        return self.pair_name

    class Meta:
        app_label = 'trading_signals'


class UserOption(models.Model):
    OPTION_CHOICES = [
        ('same', 'Same As'),
        ('higher', 'Higher Than'),
        ('lower', 'Lower Than'),
    ]
    compare_option = models.CharField(max_length=50, choices=OPTION_CHOICES, default=None, null=True)
    selected = models.BooleanField(default=False)
    price_level = models.DecimalField(max_digits=5, decimal_places=5, default=0, blank=True, null=True)

    def __str__(self):
        return self.compare_option

    class Meta:
        app_label = 'trading_signals'


class UserPreference(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE, null=True, blank=True)
    time_frame = models.ForeignKey(TimeFrame, on_delete=models.CASCADE, null=True, blank=True)
    forex_pair = models.ForeignKey(ForexPair, on_delete=models.CASCADE, null=True, blank=True)
    user_option = models.ForeignKey(UserOption, on_delete=models.CASCADE, null=True, blank=True)


class PriceData(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    forex_pair = models.ForeignKey(ForexPair, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=6)
    candle_close_at = models.DateTimeField(auto_now=False, auto_now_add=False)
    time_frame = models.ForeignKey(TimeFrame, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("forex_pair", "price", "candle_close_at")
        get_latest_by = ['candle_close_at']
        app_label = 'trading_signals'

    def __str__(self):
        return f"{self.forex_pair.pair_name} - {self.candle_close_at}"


class IndicatorValue(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    forex_pair = models.ForeignKey(ForexPair, on_delete=models.CASCADE)
    indicator_type = models.ForeignKey(Indicator, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=10, decimal_places=6)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.forex_pair.pair_name} - {self.indicator_type} - {self.timestamp}"

    class Meta:
        get_latest_by = ['timestamp']
        app_label = 'trading_signals'


class IndicatorMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    alert_message = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def save_latest_alerts(cls, alert_message, user):
        # Get the IDs of the latest 5 alerts
        latest_alert_ids = cls.objects.order_by('-created_at').values_list('id', flat=True)[:1]

        # Delete the older alerts excluding the latest 5
        cls.objects.exclude(id__in=latest_alert_ids).delete()

        # Save the latest alert
        latest_alert = cls(alert_message=alert_message, user=user)
        latest_alert.save()



class PriceMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    alert_message = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def save_latest_alerts(cls, alert_message, user):
        # Get the IDs of the latest 5 alerts
        latest_alert_ids = cls.objects.order_by('-created_at').values_list('id', flat=True)[:1]

        # Delete the older alerts excluding the latest 5
        cls.objects.exclude(id__in=latest_alert_ids).delete()

        # Save the latest alert
        latest_alert = cls(alert_message=alert_message, user=user)
        latest_alert.save()


class AllertManager:
    pass


# Cares about user
class IndicatorAlert(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pair = models.ForeignKey(ForexPair, on_delete=models.CASCADE, null=True, blank=True)
    user_option = models.ForeignKey(UserOption, on_delete=models.CASCADE, null=True, blank=True)
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE, null=True, blank=True)
    time_frame = models.ForeignKey(TimeFrame, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)


# Cares about user
class PriceAlert(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    forex_pair = models.ForeignKey(ForexPair, on_delete=models.CASCADE)
    price_level = models.DecimalField(max_digits=10, decimal_places=6)
    actual_price = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True, default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.forex_pair.pair_name} - {self.price_level}"

    class Meta:
        app_label = 'trading_signals'
