from django import forms

from .models import Customer, Supplier


class PartnerBaseForm(forms.ModelForm):
    class Meta:
        fields = (
            "name",
            "contact_person",
            "email",
            "phone",
            "address",
            "tax_id",
            "is_active",
        )

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Company name",
                }
            ),
            "contact_person": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Contact person",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "email@example.com",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "+380...",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Address",
                }
            ),
            "tax_id": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Tax ID",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-checkbox",
                }
            ),
        }


class CustomerForm(PartnerBaseForm):
    class Meta(PartnerBaseForm.Meta):
        model = Customer


class SupplierForm(PartnerBaseForm):
    class Meta(PartnerBaseForm.Meta):
        model = Supplier
