from django import forms
from tinymce.widgets import TinyMCE

from .models import Journal, Strategy, PhotoAttachment, BeforeTradeData, StrategyDoc, Asset


class JournalForm(forms.ModelForm):
    class Meta:
        model = Journal
        exclude = ['notes', "open_close", "created_at", "numbering", "r_r", "user", "day", "session", "profit"]

    pair = forms.ModelChoiceField(
        queryset=Asset.objects.all(),
        empty_label="Select Currency Pair",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_pair'}),
        label=""
    )
    buy_sell = forms.ChoiceField(choices=Journal.BuySell.choices, required=True, widget=forms.widgets.Select(
        attrs={"placeholder": "Buy/Sell", "class": "form-control"}), label="")
    time_frame = forms.ChoiceField(choices=Journal.TimeFrame.choices, required=True, widget=forms.widgets.Select(
        attrs={"placeholder": "Time Frame", "class": "form-control"}), label="TimeFrame")
    win_loss = forms.ChoiceField(choices=Journal.WinLoss.choices, required=True, widget=forms.widgets.Select(
        attrs={"placeholder": "Win/Loss", "class": "form-control"}), label="")
    entry_price = forms.DecimalField(required=True, widget=forms.widgets.NumberInput(
        attrs={"placeholder": "Entry Price", 'step': '0.000001', "class": "form-control"}), label="")
    exit_price = forms.DecimalField(required=False, widget=forms.widgets.NumberInput(
        attrs={"placeholder": "Exit Price", 'step': '0.00001', "class": "form-control"}), label="")
    tp_price = forms.DecimalField(required=True, widget=forms.widgets.NumberInput(
        attrs={"placeholder": "Tp Price", 'step': '0.000001', "class": "form-control"}), label="")
    sl_price = forms.DecimalField(required=True, widget=forms.widgets.NumberInput(
        attrs={"placeholder": "Sl Price", 'step': '0.000001', "class": "form-control"}), label="")
    position_size = forms.FloatField(required=True, widget=forms.widgets.NumberInput(
        attrs={"placeholder": "Position Size", 'step': '0.01', "class": "form-control"}), label="")
    entry_time = forms.DateTimeField(required=True, widget=forms.widgets.DateTimeInput(
        attrs={"placeholder": "Entry Time", 'type': 'datetime-local', "class": "form-control"}), label="Entry Time")
    exit_time = forms.DateTimeField(required=False, widget=forms.widgets.DateTimeInput(
        attrs={"placeholder": "Exit Time", 'type': 'datetime-local', "class": "form-control"}), label="Exit Time")
    strategy = forms.ModelChoiceField(queryset=Strategy.objects.all(), required=True, widget=forms.widgets.Select(
        attrs={"placeholder": "Trading Strategy", "class": "form-control"}), label="Strategy")
    fees = forms.DecimalField(required=True, widget=forms.widgets.NumberInput(
        attrs={"placeholder": "Fees", 'step': '0.00001', "class": "form-control"}), label="")
    rating = forms.ChoiceField(choices=Journal.Rating.choices, required=True,
                               widget=forms.widgets.Select(attrs={"placeholder": "Rating", "class": "form-control"}),
                               label="Rating")


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class PhotoForm(forms.ModelForm):
    notes = forms.CharField(widget=TinyMCE(attrs={"cols": 80, "rows": 30}), required=False)

    # image = forms.ImageField()
    class Meta:
        model = PhotoAttachment
        fields = ['images', "notes"]
        widgets = {
            'images': forms.ClearableFileInput(attrs={'multiple': False}),
            "notes": forms.Textarea(attrs={"placeholder": "", 'style': 'display: none;'})
        }

    def clean_notes(self):
        notes = self.cleaned_data['notes']

        # Clean the text from horizontal spaces
        cleaned_notes = ' '.join(notes.split())

        # Clean the text from vertical spaces
        cleaned_notes = "\n".join([line.strip() for line in cleaned_notes.splitlines()])

        return cleaned_notes


class BeforeTradeDataForm(forms.ModelForm):
    notes = forms.CharField(widget=TinyMCE(attrs={"cols": 80, "rows": 30}), required=False)

    class Meta:
        model = BeforeTradeData
        fields = ['images', 'notes']
        widgets = {
            'images': forms.ClearableFileInput(attrs={'multiple': False}),
            "notes": forms.Textarea(attrs={"placeholder": "", 'style': 'display: none;'})
        }

    def clean_notes(self):
        notes = self.cleaned_data['notes']

        # Clean the text from horizontal spaces
        cleaned_notes = ' '.join(notes.split())

        # Clean the text from vertical spaces
        cleaned_notes = "\n".join([line.strip() for line in cleaned_notes.splitlines()])

        return cleaned_notes


class ActiveRecordForm(forms.ModelForm):
    class Meta:
        model = Journal
        fields = ["pair", "buy_sell", "time_frame", "entry_price",
                  "tp_price", "sl_price", "position_size", "entry_time", "strategy"]

    pair = forms.ModelChoiceField(
        queryset=Asset.objects.all(),
        empty_label="Select Currency Pair",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_pair'}),
        label=""
    )
    buy_sell = forms.ChoiceField(choices=Journal.BuySell.choices, required=True, widget=forms.widgets.Select(
        attrs={"placeholder": "Buy/Sell", "class": "form-control"}), label="")
    time_frame = forms.ChoiceField(choices=Journal.TimeFrame.choices, required=True, widget=forms.widgets.Select(
        attrs={"placeholder": "Time Frame", "class": "form-control"}), label="TimeFrame")
    entry_price = forms.DecimalField(required=True, widget=forms.widgets.NumberInput(
        attrs={"placeholder": "Entry Price", 'step': '0.00001', "class": "form-control"}), label="")
    tp_price = forms.DecimalField(required=True, widget=forms.widgets.NumberInput(
        attrs={"placeholder": "Tp Price", 'step': '0.00001', "class": "form-control"}), label="")
    sl_price = forms.DecimalField(required=True, widget=forms.widgets.NumberInput(
        attrs={"placeholder": "Sl Price", 'step': '0.00001', "class": "form-control"}), label="")
    position_size = forms.FloatField(required=True, widget=forms.widgets.NumberInput(
        attrs={"placeholder": "Position Size", 'step': '0.01', "class": "form-control"}), label="")
    entry_time = forms.DateTimeField(required=True, widget=forms.widgets.DateTimeInput(
        attrs={"placeholder": "Entry Time", 'type': 'datetime-local', "class": "form-control"}), label="Entry Time")
    strategy = forms.ModelChoiceField(queryset=Strategy.objects.all(), required=True, widget=forms.widgets.Select(
        attrs={"placeholder": "Trading Strategy", "class": "form-control"}), label="Strategy")
    rating = forms.ChoiceField(choices=Journal.Rating.choices, required=True,
                               widget=forms.widgets.Select(attrs={"placeholder": "Rating", "class": "form-control"}),
                               label="Rating")


class CloseTradeForm(forms.ModelForm):
    class Meta:
        model = Journal
        fields = ["win_loss", "r_r", "profit", "exit_price", "exit_time", "fees"]

    win_loss = forms.ChoiceField(choices=Journal.WinLoss.choices, required=True, widget=forms.widgets.Select(
        attrs={"placeholder": "Win/Loss", "class": "form-control"}), label="")
    profit = forms.FloatField(required=True, widget=forms.widgets.NumberInput(
        attrs={"placeholder": "P/L", 'step': '0.00001', "class": "form-control"}), label="")
    exit_price = forms.DecimalField(required=False, widget=forms.widgets.NumberInput(
        attrs={"placeholder": "Exit Price", 'step': '0.00001', "class": "form-control"}), label="")
    exit_time = forms.DateTimeField(required=False, widget=forms.widgets.DateTimeInput(
        attrs={"placeholder": "Exit Time", 'type': 'datetime-local', "class": "form-control"}), label="Exit Time")
    fees = forms.DecimalField(required=True, widget=forms.widgets.NumberInput(
        attrs={"placeholder": "Fees", 'step': '0.00001', "class": "form-control"}), label="Fees")
    rating = forms.ChoiceField(choices=Journal.Rating.choices, required=True,
                               widget=forms.widgets.Select(attrs={"placeholder": "Rating", "class": "form-control"}),
                               label="Rating after")


class StrategyDocForm(forms.ModelForm):
    content = forms.CharField(widget=TinyMCE(attrs={"cols": 80, "rows": 30}))

    class Meta:
        model = StrategyDoc
        fields = ("content",)


class BeforeTradeDataEditImageForm(forms.ModelForm):
    class Meta:
        model = BeforeTradeData
        fields = ['images']


class TradeDataEditImageForm(forms.ModelForm):
    class Meta:
        model = PhotoAttachment
        fields = ['images']


class BeforeTradeDataEditNoteForm(forms.ModelForm):
    class Meta:
        model = BeforeTradeData
        fields = ['notes']

    def clean_notes(self):
        notes = self.cleaned_data['notes']

        # Clean the text from horizontal spaces
        cleaned_notes = ' '.join(notes.split())

        # Clean the text from vertical spaces
        cleaned_notes = "\n".join([line.strip() for line in cleaned_notes.splitlines()])

        return cleaned_notes


class TradeDataEditNoteForm(forms.ModelForm):
    class Meta:
        model = PhotoAttachment
        fields = ['notes']

    def clean_notes(self):
        notes = self.cleaned_data['notes']

        # Clean the text from horizontal spaces
        cleaned_notes = ' '.join(notes.split())

        # Clean the text from vertical spaces
        cleaned_notes = "\n".join([line.strip() for line in cleaned_notes.splitlines()])

        return cleaned_notes


class AddAsset(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ("name",)


class CreateNewStrategyForm(forms.ModelForm):
    class Meta:
        model = Strategy
        fields = ["title", ]

    title = forms.CharField(max_length=15, required=True,
                            widget=forms.widgets.TextInput(attrs={"placeholder": "Title", "class": "form-control"}),
                            label="")
