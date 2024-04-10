import logging

from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin)
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import (HttpResponseRedirect,
                         JsonResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import (CreateView, DetailView, ListView)
from django.views.generic.edit import UpdateView
from journal.metrics import (balance_sum, calculate_return,
                             calculate_total_profit, risk_to_reward,
                             trade_duration)
from journal.models import (Asset, BeforeTradeData, Journal, PhotoAttachment,
                            StrategyDoc)
from trading_signals.models import IndicatorMessage, PriceMessage

from .forms import (ActiveRecordForm, AddAsset, BeforeTradeDataEditImageForm,
                    BeforeTradeDataEditNoteForm, BeforeTradeDataForm,
                    CloseTradeForm, CreateNewStrategyForm, JournalForm,
                    PhotoForm, StrategyDocForm, TradeDataEditImageForm,
                    TradeDataEditNoteForm)
from .mixins import SecureUsersOperationsMixin
from .models import Day, Session, StartingDetails
from .utils import get_current_trading_session

log = logging.getLogger("journal")


# Main journal page.
class HomeView(LoginRequiredMixin, ListView):
    paginate_by = 10
    model = Journal
    template_name = "home.html"
    context_object_name = "journal"

    def get_queryset(self):
        return Journal.objects.filter(user=self.request.user).order_by("-entry_time")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all records (unpaginated)
        all_records = Journal.objects.filter(user=self.request.user).order_by("-entry_time")

        total_profit = calculate_total_profit(self.request)
        strategy_return = calculate_return(self.request)
        win_rate = risk_to_reward(self.request)
        account_balance = balance_sum(self.request)

        context["total_profit"] = total_profit
        context["strategy_return"] = strategy_return
        context["win_rate"] = win_rate
        context["account_balance"] = account_balance
        context["all_records"] = all_records

        return context


#  -------------- Getting latest alert message from db for AJAX -----------
def get_latest_alert(request):
    latest_alert_indicator = IndicatorMessage.objects.filter(user=request.user).last()
    latest_alert_pair = PriceMessage.objects.filter(user=request.user).last()

    if latest_alert_pair and latest_alert_indicator:
        if latest_alert_pair.created_at > latest_alert_indicator.created_at:
            return JsonResponse(
                {
                    "alert_id": latest_alert_pair.id,
                    "alert_message": latest_alert_pair.alert_message,
                    "alert_type": "price",
                }
            )

        else:
            return JsonResponse(
                {
                    "alert_id": latest_alert_indicator.id,
                    "alert_message": latest_alert_indicator.alert_message,
                    "alert_type": "indicator",
                }
            )

    elif latest_alert_pair:
        return JsonResponse(
            {
                "alert_id": latest_alert_pair.id,
                "alert_message": latest_alert_pair.alert_message,
                "alert_type": "price",
            }
        )

    elif latest_alert_indicator:
        return JsonResponse(
            {
                "alert_id": latest_alert_indicator.id,
                "alert_message": latest_alert_indicator.alert_message,
                "alert_type": "indicator",
            }
        )

    else:
        return JsonResponse(
            {"alert_id": None, "alert_message": "", "alert_type": "none"}
        )


# ----- Add new completed record for journal ----------
class AddRecordView(SecureUsersOperationsMixin, LoginRequiredMixin, CreateView):
    template_name = 'add_record.html'
    form_class = JournalForm

    def form_valid(self, form):
        form.instance.user = self.request.user
        user_timezone = self.request.user.timezone

        entry_time_naive = form.instance.entry_time.replace(tzinfo=None)
        current_session = get_current_trading_session(user_timezone, entry_time_naive)
        day_of_week = entry_time_naive.strftime("%A")
        day, created = Day.objects.get_or_create(day=day_of_week.capitalize())
        form.instance.day = day

        if current_session:
            form.instance.session, _ = Session.objects.get_or_create(session=current_session)

        return super().form_valid(form)

    def get_success_url(self):
        last_journal = Journal.objects.filter(user=self.request.user).latest()  # Filter by user 
        print("Last journal ID:", last_journal.pk)  # Check the last journal ID
        success_url = reverse_lazy("journal:add_photos", kwargs={"pk": last_journal.pk})
        print("Success URL:", success_url)  # Verify the success URL
        return success_url

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        print("Database entries:",
              Journal.objects.filter(user=self.request.user).values())  # Inspect the database entries
        return response


#  This is used when you upload new trade, and you get asked for note and photo.
class AddBeforeDataCreateView(SecureUsersOperationsMixin, LoginRequiredMixin, CreateView):
    form_class = BeforeTradeDataForm
    template_name = "add_data_before.html"
    success_url = reverse_lazy('journal:before-trade-data')

    def form_valid(self, form):
        # Get the last created journal record where exit_time or exit_price is None.
        last_journal = Journal.objects.filter(exit_time__isnull=True).last()
        if last_journal:
            form.instance.journal = last_journal

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        referer = self.request.META.get('HTTP_REFERER')
        if referer and self.request.path in referer:
            context['saved'] = True
        return context


# Photo for trade witch will be added to finished trade or as a supplement.
class AddPhotos(SecureUsersOperationsMixin, LoginRequiredMixin, CreateView):
    form_class = PhotoForm
    model = Journal
    template_name = "photo_form.html"
    success_url = reverse_lazy('journal:add_photos')

    def get_success_url(self):
        return reverse('journal:add_photos', kwargs={'pk': self.object.journal_entry.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["journal"] = self.get_object(Journal.objects.exclude(win_loss=None).order_by("-exit_time"),
                                             pk=self.kwargs["pk"])
        context["saved"] = context["journal"].photoattachment_set.exists()
        return context

    def form_valid(self, form):
        photo_attachment = form.save(commit=False)  # Don't save yet
        photo_attachment.journal_entry = self.get_object(Journal.objects.exclude(win_loss=None).order_by("-exit_time"),
                                                         pk=self.kwargs[
                                                             "pk"])
        photo_attachment.save()
        return super().form_valid(form)


# Detail about trade you are here after clicking on id in table
class TradeRecordDetail(LoginRequiredMixin, DetailView):
    model = Journal
    template_name = "trade_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        record = get_object_or_404(self.model, pk=self.kwargs["pk"], user=self.request.user)
        context["photos"] = PhotoAttachment.objects.filter(journal_entry=record)
        context["photos_before"] = BeforeTradeData.objects.filter(journal=record)
        context["records"] = Journal.objects.filter(id=record.pk)
        context["duration"] = trade_duration(self.request, record.pk)
        return context


def delete_record(request, pk):
    try:
        with transaction.atomic():
            delete_it = Journal.objects.get(id=pk, user=request.user)
            delete_it.delete()

        messages.success(request, "Record Deleted Successfully")
        return redirect("journal:home")
    except Journal.DoesNotExist:
        messages.success(request, "There was problem delete you record")
        return redirect("journal:home")


# Called when I need add not closed trade yet
class AddActiveRecord(SecureUsersOperationsMixin, LoginRequiredMixin, CreateView):
    form_class = ActiveRecordForm
    template_name = 'in_position_form.html'
    success_url = reverse_lazy('journal:before-trade-data')

    def form_valid(self, form):
        form.instance.user = self.request.user
        user_timezone = self.request.user.timezone

        entry_time_naive = form.instance.entry_time.replace(tzinfo=None)
        current_session = get_current_trading_session(user_timezone, entry_time_naive)
        day_of_week = entry_time_naive.strftime("%A")
        day, created = Day.objects.get_or_create(day=day_of_week.capitalize())
        form.instance.day = day

        if current_session:
            form.instance.session, _ = Session.objects.get_or_create(session=current_session)
        form.save()
        return super().form_valid(form)


class CompleteRecord(LoginRequiredMixin, UpdateView):
    model = Journal
    form_class = CloseTradeForm
    template_name = "complete_record.html"
    pk_url_kwarg = 'pk'

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        journal_pk = self.kwargs['pk']
        return reverse_lazy('journal:add_photos', kwargs={'pk': journal_pk})


class StrategyListView(LoginRequiredMixin, ListView):
    model = StrategyDoc
    template_name = 'strategy_list.html'
    context_object_name = 'strategies'

    def get_queryset(self):
        return self.model.objects.filter(strategy__user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CreateNewStrategyForm()
        return context

    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset()  # Retrieve the queryset of objects
        form = CreateNewStrategyForm(request.POST)
        if form.is_valid():
            strategy = form.save(commit=False)  # Create the instance, but don't save yet
            strategy.user = request.user
            strategy.save()
            return redirect('journal:strategy_list')
        else:
            context = self.get_context_data(object_list=queryset)  # Pass the queryset as object_list
            context['form'] = form
            return render(request, self.template_name, context)


class StrategyDocs(SecureUsersOperationsMixin, LoginRequiredMixin, UpdateView):
    model = StrategyDoc
    form_class = StrategyDocForm
    template_name = "strategy_docs.html"

    def get_object(self, queryset=None, **filter_kwargs):
        return self.model.objects.get(id=self.kwargs["pk"], strategy__user=self.request.user)

    def form_valid(self, form):
        record = form.save()
        messages.success(self.request, "Trading Plan Updated")
        return super().form_valid(form)

    def get_success_url(self):
        record = self.get_object()
        return reverse_lazy('journal:strategy_docs', kwargs={'pk': record.pk})


""" def handle_new_strategy_form(request):
    if request.method == 'POST':
        form = CreateNewStrategyForm(request.POST)
        if form.is_valid():
            strategy = form.save(commit=False)
            strategy.user = request.user  # Associate the user
            strategy.save()
            return redirect('journal:strategy_list')  # Adjust your redirect as needed
    else:
        form = CreateNewStrategyForm()  # Create an empty form for GET requests

    return render(request, 'strategy_list.html', {'form': form}) 
     # Replace this with the actual success URL
     
    
class CreateNewStrategyView(LoginRequiredMixin, TemplateView):
    template_name = "strategy_list.html"

    def dispatch(self, request, *args, **kwargs):
        return handle_new_strategy_form(request)
 """


class EditRecord(SecureUsersOperationsMixin, LoginRequiredMixin, UpdateView):
    model = Journal
    template_name = "edit_record.html"
    form_class = JournalForm
    success_url = reverse_lazy('journal:home')

    def form_valid(self, form):
        form.instance.user = self.request.user
        user_timezone = self.request.user.timezone

        entry_time_naive = form.instance.entry_time.replace(tzinfo=None)
        current_session = get_current_trading_session(user_timezone, entry_time_naive)
        day_of_week = entry_time_naive.strftime("%A")
        day, created = Day.objects.get_or_create(day=day_of_week.capitalize())
        form.instance.day = day

        if current_session:
            form.instance.session, _ = Session.objects.get_or_create(session=current_session)
        form.save()
        return super().form_valid(form)


class EditActiveRecordView(SecureUsersOperationsMixin, LoginRequiredMixin, UpdateView):
    form_class = ActiveRecordForm
    template_name = 'edit_active_record.html'
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('journal:home')

    def form_valid(self, form):
        form.instance.user = self.request.user
        user_timezone = self.request.user.timezone
        entry_time_naive = form.instance.entry_time.replace(tzinfo=None)
        current_session = get_current_trading_session(user_timezone, entry_time_naive)
        print(f"current_session {current_session}")
        day_of_week = entry_time_naive.strftime("%A")
        day, created = Day.objects.get_or_create(day=day_of_week.capitalize())
        form.instance.day = day
        if current_session:
            session, _ = Session.objects.get_or_create(session=current_session)
            form.instance.session = session
            self.model.session = session
            self.model.save()
            form.save()
        response = super().form_valid(form)
        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class EditPhotoBeforeView(SecureUsersOperationsMixin, LoginRequiredMixin, UpdateView):
    model = BeforeTradeData
    form_class = BeforeTradeDataEditImageForm
    template_name = 'edit_photo_before.html'

    def get_object(self, queryset=None, **filter_kwargs):
        if queryset is None:
            queryset = self.get_queryset()
            print(f"queryset ---------------> {queryset}")
        user = self.request.user
        pk = self.kwargs.get('pk')
        photo = get_object_or_404(queryset, pk=pk)

        if photo.journal.user != user:
            raise PermissionDenied

        return photo

    def get_success_url(self):
        photo = self.get_object(queryset=None)
        return reverse_lazy('journal:photos', kwargs={'pk': photo.journal.id})


class EditPhotoView(SecureUsersOperationsMixin, LoginRequiredMixin, UpdateView):
    form_class = TradeDataEditImageForm
    model = PhotoAttachment
    template_name = "edit_photo.html"

    def get_object(self, queryset=None, **filter_kwargs):
        if queryset is None:
            queryset = self.get_queryset()
            print(f"queryset ---------------> {queryset}")
        user = self.request.user
        pk = self.kwargs.get('pk')
        photo = get_object_or_404(queryset, pk=pk)

        if photo.journal_entry.user != user:
            raise PermissionDenied

        return photo

    def get_success_url(self):
        photo = self.get_object(queryset=None)
        return reverse_lazy('journal:photos', kwargs={'pk': photo.journal_entry.id})


class EditNoteBeforeView(SecureUsersOperationsMixin, LoginRequiredMixin, UpdateView):
    form_class = BeforeTradeDataEditNoteForm
    model = BeforeTradeData
    template_name = "edit_before_note.html"

    def get_object(self, queryset=None, **filter_kwargs):
        if queryset is None:
            queryset = self.get_queryset()
            print(f"queryset ---------------> {queryset}")
        user = self.request.user
        pk = self.kwargs.get('pk')

        photo = get_object_or_404(queryset, pk=pk)

        if photo.journal.user != user:
            raise PermissionDenied

        return photo

    def get_success_url(self):
        data = self.get_object()
        print(data)
        return reverse_lazy('journal:photos', kwargs={'pk': data.journal.id})


class EditNoneAfter(LoginRequiredMixin, UpdateView):
    form_class = TradeDataEditNoteForm
    model = PhotoAttachment
    template_name = "edit_note.html"

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
            print(f"queryset ---------------> {queryset}")
        user = self.request.user
        pk = self.kwargs.get('pk')

        photo = get_object_or_404(queryset, pk=pk)

        if photo.journal_entry.user != user:
            raise PermissionDenied
        return photo

    def get_success_url(self):
        data = self.get_object()
        return reverse_lazy('journal:photos', kwargs={'pk': data.journal_entry.id})


def delete_data_before(request, pk):
    data_delete = BeforeTradeData.objects.get(id=pk)
    data_delete.delete()
    messages.success(request, "Record Deleted Successfully")
    return redirect("journal:trade-detail", pk=data_delete.journal.id)


def delete_data(request, pk):
    data_delete = PhotoAttachment.objects.get(id=pk)
    data_delete.delete()
    messages.success(request, "Record Deleted Successfully")
    return redirect("journal:trade-detail", pk=data_delete.journal_entry.id)


# + button for adding more photos in photo page for photo-before
def add_or_restore_before_data(request, pk):
    journal = Journal.objects.get(id=pk, user=request.user)

    if request.method == "POST":
        form = BeforeTradeDataForm(request.POST, request.FILES)
        if form.is_valid():
            image = request.FILES.get("images")
            notes = request.POST.get("notes")
            instances1 = []
            instance = BeforeTradeData(journal=journal, images=image, notes=notes)
            instances1.append(instance)
            PhotoAttachment.objects.bulk_create(instances1)
            messages.success(request, "Data Uploaded Successfully")
            saved = True
            form = BeforeTradeDataForm()
            return render(
                request,
                "add_data_before.html",
                {"form": form, "saved": saved, "journal": journal},
            )
    else:
        form = BeforeTradeDataForm()

    return render(request, "add_data_before.html", {"form": form, "journal": journal})


class PhotosView(LoginRequiredMixin, DetailView):
    model = Journal
    template_name = 'photos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        record = get_object_or_404(self.model, pk=self.kwargs["pk"],
                                   user=self.request.user)
        context["record"] = record
        context['photos'] = PhotoAttachment.objects.filter(journal_entry=record)
        context['photos_before'] = BeforeTradeData.objects.filter(journal=record)
        return context


# This is un used for now
def assets(request):
    assets = Asset.objects.all()
    categories = StartingDetails.objects.filter(user=request.user).first()
    sectors = categories.selected_sectors.all()
    return render(
        request,
        "assets.html",
        {
            "assets": assets,
            "sectors": sectors,
        },
    )


# This is used for now
def add_new_asset(request):
    if request.method == "POST":
        form = AddAsset(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Pair Added")
        else:
            messages.error(request, "There was a problem adding you data")
    else:
        form = AddAsset()

    return render(request, "add_asset.html", {"form": form})


# This is for setting color to session for coloring record.
def set_color(request, record_id):
    if request.method == "POST":
        color = request.POST.get("color")
        print("color-------------------------->", color)
        request.session[f"color_{record_id}"] = color
        request.session.save()
        print("session ------------------>", request.session[f"color_{record_id}"])
        return JsonResponse({"status": "success"})
    else:
        return JsonResponse({"status": "error"})


def search_view(request):
    if request.method == 'GET':
        search_term = request.GET.get('searchTerm')
        if search_term:
            filtered_data = Journal.objects.filter(user=request.user, entry_time__icontains=search_term).values_list(
                'id', flat=True)
        else:
            filtered_data = []

        return JsonResponse({'filtered_data': list(filtered_data), 'search_active': bool(search_term)})


def search_active(request):
    if request.method == 'GET':
        search_active = request.GET.get('search_active', 'false')
        search_active = search_active.lower() == 'true'
        print(f'search_active: {search_active}')
        return render(request, 'home.html', {'search_active': search_active})
    else:
        return JsonResponse({'error': 'This endpoint only accepts AJAX requests.'}, status=400)
