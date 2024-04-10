from rest_framework import serializers
from journal.models import Journal, Asset


class JournalSerializer(serializers.ModelSerializer):
    pair = serializers.CharField(source='pair.name')
    day = serializers.CharField(source='day.day')

    class Meta:
        model = Journal
        fields = ('pair', 'entry_time', 'win_loss', 'buy_sell', 'numbering', 'day')