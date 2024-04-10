from datetime import datetime, timezone
import datetime
import pytz
from django.db import migrations, models
from currency_converter import CurrencyConverter
from django.http import JsonResponse
from django.db.models import Q
from datetime import datetime, time

from . models import Asset, BeforeTradeData

""" def get_current_trading_session(user_timezone, entry_time):
    user_tz = pytz.timezone(user_timezone)
    now_user_time = entry_time.astimezone(user_tz)  # Localize the entry time using the user's timezone
    print("Now user time: ", now_user_time)

    session_timings = {
        "New York": (user_tz.localize(datetime.datetime(now_user_time.year, now_user_time.month, now_user_time.day, 12, 0)),
                     user_tz.localize(datetime.datetime(now_user_time.year, now_user_time.month, now_user_time.day, 21, 0))),
        "London": (user_tz.localize(datetime.datetime(now_user_time.year, now_user_time.month, now_user_time.day, 7, 0)),
                   user_tz.localize(datetime.datetime(now_user_time.year, now_user_time.month, now_user_time.day, 16, 0))),
        "Sydney": (user_tz.localize(datetime.datetime(now_user_time.year, now_user_time.month, now_user_time.day, 21, 0)),
                   user_tz.localize(datetime.datetime(now_user_time.year, now_user_time.month, now_user_time.day, 6, 0)) + datetime.timedelta(days=1)),
        "Tokyo": (user_tz.localize(datetime.datetime(now_user_time.year, now_user_time.month, now_user_time.day, 23, 0)),
                  user_tz.localize(datetime.datetime(now_user_time.year, now_user_time.month, now_user_time.day, 8, 0)) + datetime.timedelta(days=1)),
    }

    for session_name, (start_time, end_time) in session_timings.items():
        if start_time <= now_user_time <= end_time:
            print(f"current_session {session_name}")
            return session_name

    return None """

trading_sessions = {
    'Asia': {'start_time': time(0, 0), 'end_time': time(8, 0)},
    'Europe': {'start_time': time(9, 0), 'end_time': time(16, 0)},
    'US': {'start_time': time(12, 0), 'end_time': time(23, 0)}
}


def get_current_trading_session(timezone, entry_time):
    # Get the trader's local time zone
    trader_timezone = pytz.timezone(timezone)
    
    # Convert the entry trade time to the trader's time zone
    entry_trade_time = pytz.utc.localize(entry_time).astimezone(trader_timezone)
    
    # Determine the trading session based on the entry trade time
    for session, times in trading_sessions.items():
        start_time = datetime.combine(entry_trade_time.date(), times['start_time']).replace(tzinfo=trader_timezone)
        end_time = datetime.combine(entry_trade_time.date(), times['end_time']).replace(tzinfo=trader_timezone)
        if start_time <= entry_trade_time < end_time:
            return session
    return 'Night Time'

    
def fix_journal_pairs(apps, schema_editor):
    Journal = apps.get_model('journal', 'Journal')
    Asset = apps.get_model('journal', 'Asset')

    for journal in Journal.objects.all():
        # Ensure an Asset exists, creating it if necessary
        asset, created = Asset.objects.get_or_create(name=journal.pair)
        journal.pair_id = asset.id 
        journal.save()


class Migration(migrations.Migration):
    dependencies = [
        ('journal', '0014_previous_migration'),
    ]

    operations = [
        migrations.RunPython(fix_journal_pairs), 
    ]


def get_pairs(request):
    term = request.GET.get('term')
    pairs = Asset.objects.filter(name__icontains=term)
    results = [{'id': pair.id, 'text': pair.name} for pair in pairs]
    return JsonResponse({'results': results})