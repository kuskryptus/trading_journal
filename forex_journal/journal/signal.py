from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from trading_signals.models import IndicatorMessage
from trading_signals.models import PriceAlert
from trading_signals.tasks import notification_pair
from django.db.models import F
from .models import Journal


# Function called when record from main table is deleted.
@receiver(post_delete, sender=Journal)
def update_record_numbering(sender, instance, **kwargs):
    user = instance.user_id
    remaining_records = Journal.objects.filter(user=user).order_by('-entry_time').values_list('id', flat=True)
  
    for idx, record_id in enumerate(remaining_records, start=1):
        Journal.objects.filter(id=record_id).update(numbering=idx)


# Function called when record from main table is added.
@receiver(post_save, sender=Journal)
def update_record_numbering(sender, instance, created, **kwargs):
    user = instance.user 

    if created:
        existing_records = Journal.objects.filter(user=user).exclude(id=instance.id).order_by('-entry_time').values_list('id', flat=True)
        total_existing_records = existing_records.count() + 1

        for idx, record_id in enumerate(existing_records, start=1):
            new_numbering = total_existing_records - idx
            Journal.objects.filter(id=record_id).update(numbering=new_numbering)
    
    remaining_records = Journal.objects.filter(user=user).order_by('-entry_time').values_list('id', flat=True)
   
    for idx, record_id in enumerate(remaining_records, start=1):
        Journal.objects.filter(id=record_id).update(numbering=idx)


@receiver(post_save, sender=IndicatorMessage)
def handle_alert_post_save(sender, instance, created, **kwargs):
    if created:
        cache.set('latest_alert_message', instance.alert_message, timeout=None)


@receiver(post_save, sender=PriceAlert)
def price_alert_post_save(sender, instance, **kwargs):
    if instance.price_level == instance.actual_price:
        print("Price level and actual price are the same!")
        instance.is_active = False
        instance.save()