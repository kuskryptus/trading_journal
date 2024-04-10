import logging

from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import FormView

log = logging.getLogger("journal") 


class UserOwnsDataMixin(AccessMixin):
    """
    Ensures user ownership of data. Customizes behavior for unauthorized access.

    """
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user)
    
    """ def dispatch(self, request, *args, **kwargs):
        obj = self.get_object() if hasattr(self, 'get_object') else None 

        if not request.user.is_authenticated:
            return redirect('accounts:login')  # Redirect to login

        if obj and self.request.user != obj.user:
            return redirect('accounts:register')  # Redirect to register

        return super().dispatch(request, *args, **kwargs) """
    
    
class SecureUsersOperationsMixin(LoginRequiredMixin, AccessMixin, FormView):
    """
    Combines security for saving and retrieving user-owned objects.
    """
    
    def form_valid(self, form):
        try:
            form.instance.user = self.request.user
            messages.success(self.request, 'Data Uploaded Successfully')
            return super().form_valid(form)
        except Exception as e:
            log.info(e)
    
    def filter_queryset(self, queryset):
        user = self.request.user
        return queryset.filter(user=user)
    
    def get_object(self, queryset=None, **filter_kwargs):    
        if queryset is None:
            queryset = self.get_queryset()
        user = self.request.user
        pk = self.kwargs.get('pk') # Get the pk from the URL
        obj = get_object_or_404(queryset, user=user, pk=pk)
        return obj