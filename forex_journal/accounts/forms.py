from accounts.models import CustomUser
from django import forms
from django.contrib.auth.models import Group
from django_select2.forms import Select2Widget
from journal.models import StartingDetails


class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'timezone']

        widgets = {
            'timezone': forms.HiddenInput(attrs={'id': 'timezone'})
        }

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.timezone = self.cleaned_data.get('timezone', '')
        print("user-timezone---------------->", user.timezone)
        users_group, created = Group.objects.get_or_create(name='Users')
        if commit:
            user.save()
            user.groups.add(users_group)
        return user


class OnboardingForm(forms.ModelForm):
    class Meta:
        model = StartingDetails
        fields = ["exchange", "starting_balance", "trading_style", "currency"]
        widgets = {
            "exchange": forms.Select(attrs={"class": "form-select"}),
            "starting_balance": forms.NumberInput(attrs={"class": "form-control"}),
            "trading_style": forms.Select(attrs={"class": "form-select"}),
            'currency': Select2Widget,
        }
        help_texts = {
            "starting_balance": "Enter your initial account balance.",
        }


class Onboarding1(forms.Form):
    trading_sectors = forms.MultipleChoiceField(
        choices=[],  # We'll populate this dynamically in the view
        widget=forms.CheckboxSelectMultiple,
    )
