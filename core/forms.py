from django import forms

from .models import SystemSettings


class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings

        fields = (
            "company_name",
            "sales_order_prefix",
            "purchase_order_prefix",
            "default_reorder_level",
            "low_stock_notifications_enabled",
            "order_notifications_enabled",
            "items_per_page",
            "company_description",
        )

        widgets = {
            "company_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "sales_order_prefix": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "purchase_order_prefix": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "default_reorder_level": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                }
            ),
            "items_per_page": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                }
            ),
            "low_stock_notifications_enabled": (
                forms.CheckboxInput(
                    attrs={
                        "class": "form-checkbox",
                    }
                )
            ),
            "order_notifications_enabled": (
                forms.CheckboxInput(
                    attrs={
                        "class": "form-checkbox",
                    }
                )
            ),
            "company_description": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
        }

    def clean_sales_order_prefix(self):
        value = self.cleaned_data["sales_order_prefix"].strip().upper()

        if not value:
            raise forms.ValidationError("Sales order prefix is required.")

        return value

    def clean_purchase_order_prefix(self):
        value = self.cleaned_data["purchase_order_prefix"].strip().upper()

        if not value:
            raise forms.ValidationError("Purchase order prefix is required.")

        return value

    def clean_items_per_page(self):
        value = self.cleaned_data["items_per_page"]

        if value > 100:
            raise forms.ValidationError("Items per page cannot exceed 100.")

        return value
