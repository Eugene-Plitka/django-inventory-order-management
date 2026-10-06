from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
)
from django.contrib.auth.models import Group

from .models import User


ROLE_NAMES = (
    "Administrator",
    "Sales Manager",
    "Purchasing Manager",
    "Warehouse Employee",
)


class WebLoginForm(AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(
            request=request,
            *args,
            **kwargs,
        )

        self.fields["username"].label = "Email"

        self.fields["username"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "you@example.com",
                "autocomplete": "email",
                "autofocus": True,
            }
        )

        self.fields["password"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Enter your password",
                "autocomplete": "current-password",
            }
        )


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Temporary password",
                "autocomplete": "new-password",
            }
        )
    )

    role = forms.ModelChoiceField(
        queryset=Group.objects.none(),
        empty_label=None,
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "is_active",
        )

        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "user@example.com",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "First name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Last name",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-checkbox",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["role"].queryset = Group.objects.filter(
            name__in=ROLE_NAMES
        ).order_by("name")

    def save(self, commit=True):
        user = super().save(commit=False)

        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

            user.groups.set([self.cleaned_data["role"]])

        return user


class UserUpdateForm(forms.ModelForm):
    role = forms.ModelChoiceField(
        queryset=Group.objects.none(),
        empty_label=None,
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "is_active",
        )

        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-checkbox",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        roles = Group.objects.filter(name__in=ROLE_NAMES).order_by("name")

        self.fields["role"].queryset = roles

        if self.instance.pk:
            current_role = self.instance.groups.filter(name__in=ROLE_NAMES).first()

            if current_role:
                self.fields["role"].initial = current_role

    def save(self, commit=True):
        user = super().save(commit=commit)

        if commit:
            user.groups.set([self.cleaned_data["role"]])

        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
        )

        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "First name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Last name",
                }
            ),
        }


class WebPasswordChangeForm(PasswordChangeForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(
            user,
            *args,
            **kwargs,
        )

        self.fields["old_password"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Current password",
            }
        )

        self.fields["new_password1"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "New password",
            }
        )

        self.fields["new_password2"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Repeat new password",
            }
        )
