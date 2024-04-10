from typing import Any

from django import forms
from trading_signals.models import (ForexPair, Indicator, PriceAlert,
                                    TimeFrame, UserOption)


class ForexPairSelectionForm(forms.Form):
    available_pairs = forms.ModelMultipleChoiceField(queryset=ForexPair.objects.all(),
                                                     widget=forms.CheckboxSelectMultiple
                                                     (attrs={'class': 'custom-checkbox'}), )
    """  selected_pairs = forms.CharField(widget=forms.Textarea(attrs={"class":'custom-textarea auto-resize'}), initial="") """
    available_indicators = forms.ModelMultipleChoiceField(
        queryset=Indicator.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "custom-checkbox2"}),
    )

    def clean(self):
        available_indicators = self.cleaned_data["available_indicators"]
        selected_indicators = [indicator.label for indicator in available_indicators]
        self.cleaned_data['selected_indicators'] = ', '.join(selected_indicators)

        return self.cleaned_data


class ForexPairFormRemove(forms.Form):
    pairs_to_remove = forms.ModelMultipleChoiceField(
        queryset=ForexPair.objects.filter(selected=True),
        widget=forms.CheckboxSelectMultiple
    )


class UserOptionForm(forms.ModelForm):
    class Meta:
        model = UserOption
        fields = ['compare_option']


class TimeFrameForm(forms.Form):
    available_time_frames = forms.ModelMultipleChoiceField(
        queryset=TimeFrame.objects.all(),
        label='Choose a time frame',
        widget=forms.CheckboxSelectMultiple(attrs={"class": "custom-checkbox-time-frame"})
    )


class PriceAlertForm(forms.ModelForm):
    class Meta:
        model = PriceAlert
        fields = ["forex_pair", "price_level"]
