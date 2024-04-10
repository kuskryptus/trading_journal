import logging

from django.db.models import DurationField, ExpressionWrapper, F, Sum
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import Journal, StartingDetails
from currency_converter import CurrencyConverter
from django.urls import reverse

log = logging.getLogger("journal")


def calculate_total_profit(request):

    p_and_l = Journal.objects.filter(user=request.user).aggregate(profit_sum=Sum("profit"))  # TODO link with strategy
    fees = Journal.objects.filter(user=request.user).aggregate(fees_sum=Sum("fees"))  # TODO link with strategy
    if len(p_and_l) or len(fees) > 1:
        fees_sum = fees.get("fees_sum", 0.0)
        rounded_fees_sum = round(fees_sum, 3) if fees_sum is not None else 0.0

        profit_sum = p_and_l.get("profit_sum", 0.0)
        rounded_profit_sum = round(profit_sum, 4) if profit_sum is not None else 0.0
        print("profit sum", rounded_profit_sum, "------" "fees_sum", rounded_fees_sum)

        total_profit = float(rounded_fees_sum) + float(rounded_profit_sum)
        total_profit = round(total_profit, 4)

        return total_profit
    else:
        messages.warning(request, "Add your first trade!")
        return "0 "


def calculate_return(request):
    starting = StartingDetails.objects.filter(user=request.user).first()
    if starting:
        starting_balance = float(starting.starting_balance)
        p_and_l = calculate_total_profit(request)
        actual_balance = p_and_l + starting_balance
        account_percentage = ((actual_balance - starting_balance)/starting_balance) * 100
        account_percentage = round(account_percentage, 3)
        return account_percentage
    else:
       
        return "0 "


def trade_duration(request,pk):
    record = Journal.objects.filter(user=request.user).get(id=pk)
    if record:
        if record.exit_time:
            duration = record.exit_time - record.entry_time
            return duration
        return None
    else:
        
        return "0 "
        

def risk_to_reward(request):
    win_count = Journal.objects.filter(user=request.user, win_loss='Win').count() # TODO link with strategy
    loss_count = Journal.objects.filter(user=request.user, win_loss="Loss").count()
    print("wind couont and loss count----------------->", win_count, loss_count)
    if win_count:
        together = Journal.objects.filter(user=request.user).count()
        win_rate = win_count/together * 100
        win_rate = round(win_rate, 3)
        return win_rate
    else:
       
        return "0 "
        

def balance_sum(request):
    starting_balance_object = StartingDetails.objects.filter(user=request.user).last()
    print(starting_balance_object)
    if starting_balance_object:
        starting_balance = starting_balance_object.starting_balance
    else:
        starting_balance = None 
    all_records = Journal.objects.filter(user=request.user).all() # TODO link with strategy

    if starting_balance and all_records:
        profits = [profit for profit in all_records.values_list('profit', flat=True) if profit is not None]
        total_balance = sum(profits) + float(starting_balance)
        print(f"Total balance:{total_balance}")
        total_balance = round(total_balance,3)
        return total_balance
    else:
        log.info(starting_balance)
        return starting_balance
        

def fees_sum():
    fees_sum = Journal.objects.all
    # TODO
    

def calculate_profit_loss(entry_price, exit_price, buy_sell, position_size):
    if buy_sell == "Buy":
        profit = (exit_price - entry_price) * position_size
    else:  # 'Sell'
        profit = (entry_price - exit_price) * position_size
    return profit