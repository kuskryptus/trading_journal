import json
import logging
import threading
import time
from collections import deque
from datetime import datetime
from accounts.models import CustomUser
import oandapyV20.endpoints.pricing as pricing
# from trading_signals.forms import
import tpqoa
from django.conf import settings
from asgiref.sync import async_to_sync
from celery import Celery, shared_task
from channels.layers import get_channel_layer
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.dispatch import Signal
from oandapyV20 import API
from oandapyV20.contrib.factories import InstrumentsCandlesFactory
from trading_signals.celery_command import (
    stop_celery_workers,
    restart_celery_beat,

)
from trading_signals.models import (ForexPair, Indicator, IndicatorAlert,
                                    IndicatorMessage, IndicatorValue,
                                    PriceAlert, PriceData, PriceMessage,
                                    TimeFrame, UserOption)
from django.core.exceptions import ObjectDoesNotExist

# celery -A forex_journal worker -lINFO --pool=threads
# docker pull rabbitmq
# celery -A forex_journal beat -l debug
# docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management
# celery -A forex_journal worker -l INFO --pool=threads -Q notification_indicator --concurrency=2
# celery -A forex_journal worker -l INFO --pool=threads -Q notification-pair --concurrency=1
log = logging.getLogger("celery.task")


def send_alert_notification(message):
    log.debug(f"Sending WebSocket notification: {message}")
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "alerts_group", {"type": "send_alert_message", "message": message}
    )


class Signal:
    def __init__(self):
        self.pairs = []
        self.indicators = []
        self.time_frames = []
        try:
            self.comparing_option = UserOption.objects.get(selected=True)
        except UserOption.DoesNotExist:
            self.comparing_option = None  # or choose a default option
        self.indicator_alert_message = []
        self.price_alerts = []
        self.live_price_for_pair = {}
        self.price_alert_message = []
        self.price_alerts_db = PriceAlert.objects.all()
        self.threads = []

    # Function called when comparing price with indicator
    def get_selected_indicator(self, user):

        active_alerts = IndicatorAlert.objects.filter(is_active=True, user=user)
        for active_alert in active_alerts:
            if active_alert:
                pair = active_alert.pair
                self.pairs.append(pair)
                indicator = active_alert.indicator
                self.indicators.append(indicator)
                time_frame = active_alert.time_frame
                self.time_frames.append(time_frame)
            else:
                log.info("No active allert found")

        log.info(
            f"pairs:{self.pairs}\n indicators:{self.indicators}\
                 \n time_frames:{self.time_frames}\n slected:{self.comparing_option}"
        )

    # Function called when comparing only with price
    # Grabing data from db to list
    def get_selected_for_comparing_price(self, user):
        self.price_alerts.clear()

        price_alerts = PriceAlert.objects.filter(is_active=True, user=user)
        if price_alerts:
            for price_alert in price_alerts:
                self.price_alerts.append(
                    {"price": price_alert.price_level, "pair": price_alert.forex_pair}
                )
        else:
            log.info("No Price Alert awailable waiting !!")

    # removing pairs from calculations
    def remove_from_selected(self, selected_pair):
        pairs = ForexPair.objects.all()
        for pair in pairs:
            if pair == selected_pair:
                pair.selected = False
                pair.save()

    def save_alert_message_indicator(self, user):
        message = self.indicator_alert_message[-1]
        log.info(f" Alert Message ------ {message}")
        if message:
            alert = IndicatorMessage(alert_message=message, user=user)
            IndicatorMessage.save_latest_alerts(message, user)
            self.indicator_alert_message.clear()
            restart_celery_beat()
            stop_celery_workers("notification_indicator")

    def save_alert_message_pair(self, user):
        message = self.price_alert_message[-1]
        log.info(f" Alert Message  Pair ------ {message}")
        if message:
            alert = PriceMessage(alert_message=message, user=user)
            PriceMessage.save_latest_alerts(message, user)
            self.indicator_alert_message.clear()

    # ----------------------------- LAST CLOSED CANDLE PRICE CALCULATION --------------------

    # ----FETCHING 5 LAST CLOSE CANDLES AND WRITING TO DB IF NOT IN DB -------
    def run_price_calculation(self, pair, time_frame, user_id):
        user = CustomUser.objects.get(pk=user_id)
        access_token = settings.OANDA_SECRET 
        client = API(access_token=access_token, environment="live")
        accountID = settings.ACCOUNT_ID
        granularity = time_frame

        params = {
            "granularity": granularity,
            "count": 5,
        }

        last_5_candles = deque(maxlen=5)

        while True:
            while True:
                request_generator = InstrumentsCandlesFactory(
                    instrument=pair, params=params
                )
                endpoint = next(request_generator)
                response = client.request(endpoint)
                log.info(response)
                forex_pair_instance = ForexPair.objects.get(pair_name=pair)
                time_frame_instance = TimeFrame.objects.get(time_frame_label=time_frame)

                try:
                    for candle in response["candles"]:
                        if candle["complete"]:
                            timestamp_str = candle["time"]
                            if "." in timestamp_str:
                                timestamp_str = timestamp_str.split(".")[0]
                            if timestamp_str.endswith("Z"):
                                timestamp_str = timestamp_str[:-1]
                            current_timestamp = datetime.strptime(
                                timestamp_str, "%Y-%m-%dT%H:%M:%S"
                            )
                            close_price = candle["mid"]["c"]

                            # Check if the candle's time and price already exist in the records
                            if any(
                                    data["time"] == current_timestamp
                                    and data["price"] == close_price
                                    for data in last_5_candles
                            ):
                                log.info("Price already processed. Skipping.")
                                continue
                            else:
                                log.info(f"New price found: {close_price}")

                                # Record the candle's time and price
                                new_data = {
                                    "time": current_timestamp,
                                    "price": close_price,
                                }
                                last_5_candles.append(new_data)
                                try:
                                    # Save the data to your database (assuming PriceData is your model)
                                    new_price = PriceData.objects.create(
                                        user=user,
                                        candle_close_at=current_timestamp,
                                        price=close_price,
                                        forex_pair=forex_pair_instance,
                                        time_frame=time_frame_instance,
                                    )
                                    new_price.save()
                                except IntegrityError:
                                    log.info(
                                        "IntegrityError: Price already exists in the database."
                                    )
                        else:
                            continue
                except Exception as e:
                    log.info(f"Error {e}")
                time.sleep(10)

    # ------ 200 CANDLES HISTORY FOR EACH PAIR  ------
    def buffer_price_data(self, pair, time_frame, user_id):
        user = CustomUser.objects.get(pk=user_id)
        access_token = settings.OANDA_SECRET 
        client = API(access_token=access_token, environment="live")
        granularity = time_frame

        params = {
            "granularity": granularity,
            "count": 201,
        }
        request_generator = InstrumentsCandlesFactory(instrument=pair, params=params)
        endpoint = next(request_generator)
        response = client.request(endpoint)
        forex_pair_instance = ForexPair.objects.get(pair_name=pair)
        time_frame_instance = TimeFrame.objects.get(time_frame_label=time_frame)
        for candle in response["candles"]:
            if candle["complete"]:
                timestamp_str = candle["time"]
                if "." in timestamp_str:
                    timestamp_str = timestamp_str.split(".")[0]
                if timestamp_str.endswith("Z"):
                    timestamp_str = timestamp_str[:-1]
                current_timestamp = datetime.strptime(
                    timestamp_str, "%Y-%m-%dT%H:%M:%S"
                )
                close_price = candle["mid"]["c"]
                try:
                    new_price = PriceData.objects.create(
                        user=user,
                        candle_close_at=current_timestamp,
                        price=close_price,
                        forex_pair=forex_pair_instance,
                        time_frame=time_frame_instance,
                    )
                    new_price.save()
                except IntegrityError:
                    log.info("IntegrityError: Price already exists in the database.")
        log.info("All candles buffered")
        log.info(response)

    # ------ 200 CANDLES HISTORY FOR EACH PAIR  ------

    def live_price_stream(self, pair, user):
        accountID = settings.ACCOUNT_ID
        api = API(
            access_token= settings.OANDA_SECRET,
            environment="live",
        )
        params = {"instruments": pair}

        r = pricing.PricingStream(accountID=accountID, params=params)
        rv = api.request(r)

        while True:
            try:
                response = next(rv)
                if response["type"] == "PRICE":
                    instrument = response["instrument"]
                    bid_price = response["bids"][0]["price"]
                    ask_price = response["asks"][0]["price"]
                    actual_price = (float(bid_price) + float(ask_price)) / 2
                    forex_pair = ForexPair.objects.get(pair_name=instrument)
                    PriceAlert.objects.filter(forex_pair=forex_pair, user=user).update(
                        actual_price=actual_price
                    )
                    log.info(f"Instrument: {instrument}, Price: {actual_price}")
            except Exception as e:
                print("Error:", e)
                break  # Exit the loop in case of an error

    def start_live_price_stream(self, pair, user):
        t1 = threading.Thread(target=self.live_price_stream, args=(pair, user))
        """ t1.daemon = True """
        t1.start()

    def terminate_threads(self):
        for thread in self.threads:
            thread.join()

    def compare_price_alerts(self, user):
        while True:
            price_alerts = PriceAlert.objects.filter(is_active=True, user=user)
            if price_alerts:
                for alert in price_alerts:
                    forex_pair = alert.forex_pair
                    price_level = float(alert.price_level)
                    actual_price = alert.actual_price

                    deviation_percentage = 0.01
                    upper_bound = price_level * (1 + deviation_percentage / 100)
                    lower_bound = price_level * (1 - deviation_percentage / 100)

                    if lower_bound <= actual_price <= upper_bound:
                        alert.is_active = False
                        alert.save()
                        log.info(
                            f"Alert: Price level for {forex_pair} has been reached or is very close !!"
                        )
                        alert_message = f"Alert: Price level for {forex_pair} has been reached or is very close !!"
                        self.price_alert_message.append(alert_message)
                        self.save_alert_message_pair(user)
                    else:
                        log.info("No alert waiting")
                    time.sleep(2)
            else:
                log.info("No active price alerts")
                time.sleep(10)

    # --------SELECTED INDICATOR CALCULATION ----------

    def calculate_indicator_price(self, pair, indicator, time_frame, user):
        if indicator == "SMA200":
            try:
                price_data = PriceData.objects.filter(user=user,
                                                      forex_pair__pair_name=pair,
                                                      time_frame__time_frame_label=time_frame,
                                                      ).order_by("candle_close_at")[:200]
                log.info(price_data)
                closing_prices = [data.price for data in price_data]
                if len(closing_prices) < 200:
                    log.warning(f"Insufficient data to calculate SMA200 for {pair}")
                    return None

                sma_200 = sum(closing_prices[200:]) / 200
                indicator_value = IndicatorValue(
                    user=user,
                    forex_pair=ForexPair.objects.get(pair_name=pair),
                    indicator_type=Indicator.objects.get(label=indicator),
                    value=sma_200,
                )
                indicator_value.save()
                log.info(f"SMA 200 for {pair}: {sma_200}")
                return sma_200

            except Exception as e:
                log.error(f"Error calculating SMA200 for {pair}: {e}")
                return None

        elif indicator == "SMA20":
            try:
                price_data = PriceData.objects.filter(user=user,
                                                      forex_pair__pair_name=pair,
                                                      time_frame__time_frame_label=time_frame,
                                                      ).order_by("candle_close_at")[:20]
                log.info(price_data)
                closing_prices = [data.price for data in price_data]
                if len(closing_prices) < 20:
                    log.warning(f"Insufficient data to calculate SMA20 for {pair}")
                    return None

                sma_20 = sum(closing_prices[20:]) / 20
                indicator_value = IndicatorValue(
                    user=user,
                    forex_pair=ForexPair.objects.get(pair_name=pair),
                    indicator_type=Indicator.objects.get(label=indicator),
                    value=sma_20,
                )
                indicator_value.save()
                return sma_20

            except Exception as e:
                log.error(f"Error calculating SMA20 for {pair}: {e}")
                return None

        elif indicator == "SMA10":
            try:
                price_data = PriceData.objects.filter(user=user,
                                                      forex_pair__pair_name=pair,
                                                      time_frame__time_frame_label=time_frame,
                                                      ).order_by("-candle_close_at", "forex_pair'")[:10]
                closing_prices = [float(data.price) for data in price_data]
                log.info(f"Closing prices {closing_prices}")

                if len(closing_prices) < 10:
                    log.info(len(closing_prices))
                    log.warning(f"Insufficient data to calculate SMA10 for {pair}")
                    return None

                sma_10 = sum(closing_prices) / 10
                log.info(f"{indicator} price is {sma_10}")
                indicator_value = IndicatorValue(
                    user=user,
                    forex_pair=ForexPair.objects.get(pair_name=pair),
                    indicator_type=Indicator.objects.get(label=indicator),
                    value=sma_10,
                )
                indicator_value.save()
                return sma_10

            except Exception as e:
                log.exception(f"Error calculating SMA10 for {pair}: {e}")
                return None
        else:
            log.warning(f"Indicator {indicator} not supported")
            return None

    # --------SELECTED INDICATOR CALCULATION ----------

    # CALLING THE FUNCTION ABOVE, THE VALUE OF THE SELECTED INDICATOR WILL BE CALCULATED FOR EACH CURRENCY PAIR
    def save_indicator_price(self, user):
        active_alerts = IndicatorAlert.objects.filter(is_active=True, user=user)

        for active_alert in active_alerts:
            if active_alert:
                user_option = active_alert.user_option
                pair = active_alert.pair.pair_name
                pair_ = active_alert.pair
                indicator = active_alert.indicator.label
                indicator_ = active_alert.indicator
                time_frame = active_alert.time_frame.time_frame_label

                self.calculate_indicator_price(pair, indicator, time_frame, user)

                alert_message = self.compare_price(user_option, pair_, indicator_, active_alert, user)
                if alert_message:
                    try:
                        log.info(f"Success: {alert_message}")
                        self.indicator_alert_message.append(alert_message)
                        self.save_alert_message_indicator(user)
                    except Exception as e:
                        log.exception(e)
                else:
                    log.info("No Match")
            else:
                log.warning("You dont have any allerts")

    # --------- COMPARISON ---- MAIN FUNCTION WHERE THE NOTIFY FUNCTION WILL BE CALLED -------
    def compare_price(self, user_option, pair, indicator, active_alert, user):
        try:
            log.info(f"user_option 453 {user_option}")
            """ comparing_option = UserOption.objects.get(compare_option=user_option) """
            latest_asset_price = PriceData.objects.filter(forex_pair=pair, user=user).latest().price
            latest_indicator_value = IndicatorValue.objects.filter(indicator_type=indicator, user=user).latest().value
            log.info(
                f"latest_asset_price {latest_asset_price}, latest_indicator_value {latest_indicator_value}")

            if user_option == UserOption.objects.get(compare_option="higher"):
                if latest_asset_price > latest_indicator_value:
                    active_alert.is_active = False
                    active_alert.save()
                    return f"Alert!!! Price of {pair} is above {indicator}!!!"

            elif user_option == UserOption.objects.get(compare_option="lower"):
                log.info(f"Option {user_option} is selected")
                if latest_asset_price < latest_indicator_value:
                    active_alert.is_active = False
                    active_alert.save()
                    log.info(
                        f"  {latest_asset_price}, latest_indicator_value {latest_indicator_value}")
                    return f"Alert!!! Price of {pair} is bellow {indicator}!!!"

            else:
                if latest_asset_price == latest_indicator_value:
                    active_alert.is_active = False
                    active_alert.save()
                    return f"Alert!!! Price of {pair} is same as {indicator}!!!"

        except PriceData.DoesNotExist:
            log.info("No price data, waiting!!")

        except IndicatorValue.DoesNotExist:
            log.info("No indicator value data, waiting!!")

        except Exception as e:
            log.exception(f"Error occurred while comparing prices: {e}")


"""  def invalidate_syganal():
    active_indicator.selected = False
    active_indicator.save()

    active_time_freame.selected = False
    active_time_freame.save()

    active_pair.selected = False
    active_pair.save()

    user_option = UserOption.objects.get(selected=True)
    user_option.selected = False
    user_option.save() """


@shared_task(queue="notification_indicator")
def process_price_for_pair(pair, time_frame, user_id):
    signal = Signal()
    signal.buffer_price_data(pair, time_frame, user_id)
    time.sleep(15)
    signal.run_price_calculation(pair, time_frame, user_id)


@shared_task(queue="notification_indicator")
def notification_indicator(**kwargs):
    user_id = kwargs.get('user_id')
    print("user id --------------------------------->", user_id)
    user = CustomUser.objects.get(pk=user_id)
    try:
        log.info("Notification task started.")
        signal = Signal()
        signal.get_selected_indicator(user)
        signal.save_indicator_price(user)
        log.info("Notification task completed.")
    except Exception as e:
        log.exception("Error in notification task: %s", e)


@shared_task(queue="notification-pair")
def notification_pair(user_id):
    user = CustomUser.objects.get(pk=user_id)
    try:
        signal = Signal()
        signal.get_selected_for_comparing_price(user)
        alerts = signal.price_alerts
        log.info(f"Alerst ---------------> {alerts}")
        for alert in alerts:
            pair = alert["pair"]
            thread = signal.start_live_price_stream(pair, user)
            signal.threads.append(thread)
        signal.compare_price_alerts(user)
    except Exception as e:
        log.exception("Error in notification_pair task: %s", e)


def remove_pair(pair):
    signal = Signal()
    signal.remove_from_selected(pair)
    log.info("Pair removed!")
