from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import ListView, TemplateView
from journal.models import BeforeTradeData, Journal, PhotoAttachment, Strategy
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core import serializers
from .serializers import JournalSerializer


# Create your views here.


class TradeDebugView(LoginRequiredMixin, ListView):
    model = Journal
    template_name = 'trade_debug_index.html'
    context_object_name = "trades"
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["trades"] = Journal.objects.filter(user=self.request.user).order_by(
            "-entry_time")  # Or any filtering you want
        return context


def search_debug(request):
    if request.method == 'POST':
        checked_checkboxes = []  # Create an empty list to store the checked checkbox names

        search_term = request.POST.get('search_text')

        # Extract the checked checkbox names from the POST data
        for key in request.POST:
            if key.endswith('_checked') and request.POST.get(key) == 'true':
                checkbox_name = key.replace('_checked', '')  # Remove the trailing '_checked' suffix
                checked_checkboxes.append(checkbox_name)

        search_term = request.POST.get('search_text')
        print("Checked checkboxes:", checked_checkboxes)
        print("Received POST data:", request.POST)

        trades = Journal.objects.filter(user=request.user)

        if search_term:  # If search term is provided
            trades_prefetch = trades.filter(
                Q(day__day__icontains=search_term) |
                Q(entry_price__icontains=search_term) |
                Q(pair__name__icontains=search_term) |
                Q(buy_sell__icontains=search_term)

            )
            print("Trades after filtering:", trades_prefetch)

        if checked_checkboxes:  # If any checkbox is checked
            if 'win_loss' in checked_checkboxes:
                if search_term.lower() == 'win':
                    trades = trades.filter(win_loss__iexact=Journal.WinLoss.WIN)
                    print("Trades after filtering:", trades)

                elif search_term.lower() == 'loss':
                    trades = trades.filter(win_loss__iexact=Journal.WinLoss.LOSS)
                    print("Trades after filtering:", trades)

            elif 'day' in checked_checkboxes:
                trades = trades_prefetch.filter(day__day__icontains=search_term)
                print("Trades:", trades)

            # Add more conditions for other checkbox names if needed

            if 'buy_sell' in checked_checkboxes:
                trades = trades_prefetch.filter(buy_sell__icontains=search_term)
                print("Trades:", trades)

            trades_data = JournalSerializer(trades, many=True).data
            print("Trades data --------------------- json:", trades_data)
            return JsonResponse({'success': True, 'trades': trades_data})

    return render(request, 'trade_debug_index.html')
