import logging
import shlex
import subprocess
from datetime import datetime, timedelta
from typing import Any
from django.shortcuts import get_object_or_404
from celery import Celery, shared_task
from django.contrib import messages
from django.core.management import call_command
from django.forms.forms import BaseForm
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.generic import FormView, TemplateView
from django.views.generic.edit import CreateView
from django_celery_beat.models import IntervalSchedule, PeriodicTask
from django.contrib.auth.decorators import login_required
from django.http import Http404
from trading_signals.celery_command import (
    restart_celery_worker,
    start_celery_worker_pair,
    stop_celery_workers,
    restart_celery_beat,
    stop_celery_workers,
)
from trading_signals.forms import (ForexPairFormRemove, ForexPairSelectionForm,
                                   PriceAlertForm, TimeFrameForm,
                                   UserOptionForm)
from trading_signals.models import (ForexPair, Indicator, IndicatorAlert,
                                    IndicatorMessage, PriceAlert, TimeFrame,
                                    UserOption, UserPreference)
from trading_signals.tasks import (Signal, notification_indicator,
                                   notification_pair, process_price_for_pair,
                                   remove_pair)

from forex_journal.celery import app

app = Celery('tasks', broker='pyamqp://guest@localhost//')

log = logging.getLogger(__name__)


@login_required
def save_notification_alert(request):
    if request.method == "POST":

        restart_celery_worker("notification_indicator")
        selected_pairs_ = ForexPair.objects.filter(selected=True).exists
        form = ForexPairSelectionForm(request.POST)
        comparing_options = UserOptionForm(request.POST)
        time_frames = TimeFrameForm(request.POST)

        if selected_pairs_:
            form2 = ForexPairFormRemove()
        if form.is_valid() and time_frames.is_valid() and comparing_options.is_valid():

            selected_indicators = form.cleaned_data["available_indicators"]
            available_pairs = form.cleaned_data["available_pairs"]
            selected_indicators = form.cleaned_data["available_indicators"]
            selected_time_frames = time_frames.cleaned_data.get("available_time_frames", [])
            selected_time_frames_list = list(selected_time_frames.values_list('time_frame_label', flat=True))
            comparing_options = comparing_options.cleaned_data["compare_option"]

            # Capturing user input and creating new indicator_ alert record
            user_options = UserOption.objects.filter(selected=True)
            for user_option in user_options:
                user_option.selected = False
                user_option.save()
            selected_option = UserOption.objects.get(compare_option=comparing_options)
            selected_option.selected = True
            selected_option.save()
            try:
                for indicator in selected_indicators:
                    for pair in available_pairs:
                        for time_frame in selected_time_frames:
                            new_alert = IndicatorAlert(
                                pair=pair,
                                user=request.user,
                                user_option=selected_option,
                                indicator=indicator,
                                time_frame=time_frame,
                                is_active=True,
                            )
                        new_alert.save()
            except Exception as e:
                log.exception(f"Error 92 {e}")

            restart_celery_beat()
            try:
                log.info("Started do you see new window ? ")
                signal = Signal()
                signal.get_selected_indicator(request.user)
                pairs = IndicatorAlert.objects.filter(is_active=True, user=request.user).values_list("pair__pair_name",
                                                                                                     flat=True).distinct()
                time_frames = IndicatorAlert.objects.filter(is_active=True, user=request.user).values_list(
                    "time_frame__time_frame_label", flat=True).distinct()
                unique_pairs = list(pairs)
                unique_time_frames = list(time_frames)
                for pair in unique_pairs:
                    for time_frame in unique_time_frames:
                        process_price_for_pair.apply_async(args=[pair, time_frame, request.user.id])
                user_id = request.user.id
                log.info("user_id------------------------------->: %s", user_id)
                call_command('start_periodic_task', user_id)
                messages.success(request, "Signal scheduled")

            except Exception as e:
                log.exception(e)

        return redirect("trading_signals:signal_management")

    else:

        form = ForexPairSelectionForm()
        time_frames = TimeFrameForm()
        comparing_options = UserOptionForm()
        price_alert_form = PriceAlertForm()

        available_pairs = ForexPair.objects.all()
        selected_pairs_ = ForexPair.objects.filter(selected=True).exists
        if selected_pairs_:
            form2 = ForexPairFormRemove()
        return render(request, "create_trading_signal.html",
                      {'form': form, "form2": form2,
                       'available_pairs': available_pairs,
                       "selected_pairs_": selected_pairs_,
                       "compare_form": comparing_options,
                       "time_frames": time_frames,
                       "price_alert_form": price_alert_form,
                       })


def remove_forex_pair(request):
    form2 = ForexPairFormRemove(request.POST or None)
    if request.method == 'POST':
        if form2.is_valid():
            selected_pairs = form2.cleaned_data.get('pairs_to_remove', [])
            for pair in selected_pairs:
                remove_pair(pair)

    return redirect("trading_signals:trading_signal")


def save_price_alert(request):
    price_alert_form = PriceAlertForm(request.POST or None)
    if request.method == "POST":
        try:
            if price_alert_form.is_valid():
                forex_pair = price_alert_form.cleaned_data["forex_pair"]
                price_level = price_alert_form.cleaned_data["price_level"]
                alert = PriceAlert.objects.create(forex_pair=forex_pair, price_level=price_level, is_active=True,
                                                  user=request.user)
                stop_celery_workers("notification-pair")  # Kill celery worker and auto start 1 
                start_celery_worker_pair()

                if alert:
                    signal = Signal()
                    signal.terminate_threads()
                    notification_pair.apply_async(args=[request.user.id])
                else:
                    log.info("There was problem creating alert")
            else:
                log.error("Price alert form was not valid")
        except Exception as e:
            log.exception(f"Error 169 :{e}")

    return redirect("trading_signals:signal_management")


def signal_management(request):
    indicator_alert = IndicatorAlert.objects.filter(user=request.user).all()
    price_alerts = PriceAlert.objects.filter(user=request.user).all()
    return render(request, "ts_management.html", {"indicator_alert": indicator_alert, "price_alerts": price_alerts})


def discard_price_alert(request, pk):
    try:
        if request.method == "POST":
            user = request.user
            restart_celery_beat()
            log.info(pk)
            alert_to_delete = PriceAlert.objects.get(id=pk, user=user)
            log.info(alert_to_delete)
            if request.user == alert_to_delete.user:
                alert_to_delete.delete()
            else:
                raise Http404("You are not authorized to delete this alert")
            stop_celery_workers("notification-pair")
            worker_process = start_celery_worker_pair()
    except Exception as e:
        log.exception(e)

    return redirect("trading_signals:signal_management")


def discard_indicator_alert(request, pk):
    if request.method == "POST":
        user = request.user
        restart_celery_beat()
        alert_to_delete = IndicatorAlert.objects.get(id=pk, user=user)
        log.info(pk)
        log.info(alert_to_delete)
        if request.user == alert_to_delete.user:
            alert_to_delete.delete()
        else:
            raise Http404("You are not authorized to delete this alert")

        restart_celery_worker("notification_indicator")

    return redirect("trading_signals:signal_management")
