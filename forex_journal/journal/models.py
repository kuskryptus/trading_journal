from django.conf import settings
import pycountry
from currency_converter import CurrencyConverter
from currency_converter import RateNotFoundError
from django.conf import settings
from django.db import models
# python manage.py dumpdata --indent=2 --exclude auth > data.json
# python manage.py loaddata data.json
# python -Xutf8 ./manage.py dumpdata --indent=2 > data.json
from tinymce import models as tinymce_models


class JournalManager(models.Manager):
    def get_queryset(self, request=None):  # Add 'request' as an optional argument
        if request and request.user.is_authenticated:  # Check if request is provided
            return super().get_queryset().filter(user=request.user)
        else:
            return super().get_queryset()


class Asset(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(default="", max_length=20, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        app_label = "journal"


class PredefinedAssets(models.Model):
    name = models.CharField(default="", max_length=20, unique=True, blank=True, null=True)
    asset = models.ForeignKey("TradingSector", on_delete=models.CASCADE, default="", blank=True, null=True)

    def __str__(self):
        return self.name


class TradingSector(models.Model):
    name = models.CharField(default="", max_length=20, unique=True, blank=True, null=True)
    selected = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Journal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    BOOL_CHOICES = [
        (True, "Open"),
        (False, "Close"),
    ]

    class BuySell(models.TextChoices):
        BUY = "Buy"
        SELL = "Sell"

    class WinLoss(models.TextChoices):
        WIN = "Win"
        LOSS = "Loss"
        NONE = "None"

    class TimeFrame(models.TextChoices):
        WEEK = "Weekly", "1W"
        DAY = "Daily", "1D"
        FOUR = "4H", "4H"
        ONE_HOUR = "1H", "1H"
        HALF_HOUR = "30MIN", "30MIN"
        FIFTEEN_MINUTES = "15MIN", "15MIN"
        FIVE_MINUTES = "5M", "5M"
        ONE_MINUTE = "1M", "1M"

    class Rating(models.TextChoices):
        ONE = "1.", "1"
        TWO = "2", "2"
        THREE = "3.", "3"
        FOUR = "4.", "4"
        FIVE = "5.", "5"
        SIX = "6", "6"
        SEVEN = "7.", "7"
        EIGHT = "8.", "8"
        NINE = "9", "9"
        TEN = "10", "10"

    numbering = models.IntegerField(default=0)
    entry_price = models.DecimalField(
        max_digits=10, decimal_places=6, blank=True, default=None, null=True
    )
    pair = models.ForeignKey(Asset, on_delete=models.CASCADE, null=True, blank=True)
    entry_time = models.DateTimeField()
    exit_time = models.DateTimeField(null=True)
    exit_price = models.DecimalField(
        max_digits=10, decimal_places=6, blank=True, default=None, null=True
    )
    buy_sell = models.CharField(
        max_length=20, choices=BuySell.choices, default=BuySell.BUY, null=True
    )

    time_frame = models.CharField(
        max_length=20, choices=TimeFrame.choices, default=TimeFrame.ONE_HOUR, null=True
    )

    win_loss = models.CharField(
        max_length=20, choices=WinLoss.choices, default=WinLoss.NONE, null=True
    )

    tp_price = models.DecimalField(
        max_digits=10, decimal_places=7, blank=True, default=None, null=True
    )
    sl_price = models.DecimalField(
        max_digits=10, decimal_places=7, blank=True, default=None, null=True
    )
    day = models.ForeignKey(
        "Day", max_length=30, default=None, on_delete=models.CASCADE
    )
    r_r = models.CharField(max_length=100, default=None, null=True)
    session = models.ForeignKey(
        "Session", max_length=30, default=None, on_delete=models.CASCADE, null=True
    )
    position_size = models.FloatField(max_length=5)
    strategy = models.ForeignKey("Strategy", on_delete=models.CASCADE, null=True)
    profit = models.FloatField(blank=True, default=None, null=True)
    fees = models.DecimalField(
        max_digits=5, decimal_places=5, default=0, blank=True, null=True
    )
    open_close = models.BooleanField(
        verbose_name="IN POSITION", null=True, default="True"
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    rating = models.CharField(
        max_length=5, choices=Rating.choices, default=Rating.ONE, null=True
    )

    def calculate_r_r(self):
        if self.tp_price is not None and self.sl_price is not None and self.user:  # Check for user
            take_profit = self.tp_price
            stop_loss = self.sl_price
            entry_price = self.entry_price

            profit_part = take_profit - entry_price
            loss_part = entry_price - stop_loss

            if loss_part != 0:
                ratio = profit_part / loss_part
                r_r = "1" + ":" + f"{round(abs(ratio), )}"
            else:
                r_r = "N/A"
            return r_r

        return None

    def get_user_currency(self, pair, profit, user, date=None):
        quote = pair.split("/")[1]
        print("quote", quote)
        user_currecny = StartingDetails.objects.filter(user=user).first().currency
        print("user_currecny", user_currecny)
        c = CurrencyConverter()
        amount = round(c.convert(profit, quote, user_currecny, date=None), 3)
        print("amount", amount)
        return amount

    def save(self, *args, **kwargs):
        if self.entry_time and not self.day:  # Ensure entry_time is not empty and day is not already set
            day_of_week = self.entry_time.strftime("%A")  # Extract day of the week from entry_time
            # Find or create Day object based on the day of the week
            self.day, created = Day.objects.get_or_create(day=day_of_week.capitalize())

        if self.tp_price is not None and self.sl_price is not None and self.user:  # Check for user
            take_profit = self.tp_price
            stop_loss = self.sl_price
            entry_price = self.entry_price

            profit_part = take_profit - entry_price
            loss_part = entry_price - stop_loss

            if loss_part != 0:
                ratio = profit_part / loss_part
                r_r = "1" + ":" + f"{round(abs(ratio), 2)}"
            else:
                r_r = "N/A"
            self.r_r = r_r
        else:
            self.r_r = None

        if self.exit_price:
            if self.buy_sell.lower() == "buy":
                self.profit = float((self.exit_price - self.entry_price)) * float(self.position_size)
            else:  # 'Sell'
                self.profit = float((self.entry_price - self.exit_price)) * float(self.position_size)
        else:
            self.profit = None

        if self.user and self.pair and self.profit:  # Check for necessary data
            try:
                converted_profit = self.get_user_currency(self.pair.name, self.profit, self.user, date=self.exit_time)
                self.profit = converted_profit  # Update profit 
            except RateNotFoundError:
                converted_profit = self.get_user_currency(self.pair.name, self.profit, self.user)
                self.profit = converted_profit

        super().save(*args, **kwargs)

    def fix_journal_pairs(self, apps, schema_editor):
        Journal = apps.get_model('journal', 'Journal')
        Asset = apps.get_model('journal', 'Asset')

        # Get or create a fallback asset
        fallback_asset, _ = Asset.objects.get_or_create(name="Other", user=settings.AUTH_USER_MODEL.objects.first())

        for journal in Journal.objects.all():
            asset, created = Asset.objects.get_or_create(name=journal.pair, user=journal.user)
            if not created:  # Asset already exists
                if asset.user != journal.user:
                    # Handle the ownership mismatch (log a warning, use fallback, etc.)
                    pass
                else:
                    asset = fallback_asset

            journal.pair_id = asset.id
            journal.save()

    class Meta:
        unique_together = ("entry_price", "entry_time")
        get_latest_by = "created_at"

    def __str__(self):
        return f"{self.pair} - {self.entry_time} - {self.buy_sell} - {self.time_frame} "

    objects = JournalManager()


class Indicator(models.Model):
    indicator = models.CharField(max_length=100, default="")

    def __str__(self):
        return self.indicator

    class Meta:
        app_label = "journal"


class Strategy(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=50, default="", primary_key=True, blank=True)
    performance = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, default=None, null=True
    )
    losing_trades = models.IntegerField(null=True, blank=True)
    winning_trades = models.IntegerField(null=True, blank=True)
    indicators = models.ManyToManyField(Indicator, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        app_label = "journal"


class PhotoAttachment(models.Model):
    journal_entry = models.ForeignKey(Journal, on_delete=models.CASCADE)
    images = models.ImageField(upload_to="image/")
    notes = tinymce_models.HTMLField(blank=True)

    class Meta:
        app_label = "journal"


class Session(models.Model):
    session = models.CharField(max_length=100, default="")

    def __str__(self):
        return self.session

    class Meta:
        app_label = "journal"


class Day(models.Model):
    day = models.CharField(max_length=20, default="")

    def __str__(self):
        return self.day

    class Meta:
        app_label = "journal"


class BeforeTradeData(models.Model):
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, default="")
    notes = tinymce_models.HTMLField(blank=True)
    images = models.ImageField(upload_to="image/")

    class Meta:
        app_label = "journal"

    def __str__(self):
        return f" Note :{self.id} belongs to {self.journal}"


class StrategyDoc(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    content = tinymce_models.HTMLField(blank=True, null=True)

    def __str__(self):
        return f"Trading Plan for strategy : {self.strategy}"

    class Meta:
        app_label = "journal"


class StartingDetails(models.Model):
    EXCHANGE_CHOICES = [
        ('oanda', 'OANDA'),
        ('ic_market', 'IC MARKET'),
        ('etoro', 'ETORO'),
        ('fxcm', 'FXCM'),
        ('ig_markets', 'IG MARKETS')
    ]

    CURRENCY_CHOICES = [
        (currency.alpha_3, currency.name)
        for currency in pycountry.currencies]

    TRADING_STYLE_CHOICES = [('all-in-one', 'All in one'),
                             ('separate', 'Separate strategies')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=1)
    exchange = models.CharField(max_length=100, choices=EXCHANGE_CHOICES, null=True, blank=True)
    assets = models.ForeignKey(Asset, on_delete=models.CASCADE, default="", blank=True, null=True)
    currency = models.CharField(max_length=20, default="", blank=True, null=True, choices=CURRENCY_CHOICES)
    starting_balance = models.DecimalField(
        max_digits=10, decimal_places=4, default=None
    )
    trading_style = models.CharField(max_length=100, default="", blank=True, null=True, choices=TRADING_STYLE_CHOICES)
    selected_sectors = models.ManyToManyField(TradingSector, blank=True)

    class Meta:
        app_label = "journal"

    def __str__(self):
        return self.exchange
