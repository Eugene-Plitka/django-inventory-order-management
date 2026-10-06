from decimal import Decimal

from django import forms
from django.db.models import Q
from django.forms import BaseFormSet, formset_factory

from catalog.models import Product
from inventory.models import Warehouse
from partners.models import Customer


class SalesOrderForm(forms.Form):
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.none(),
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.none(),
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    def __init__(
        self,
        *args,
        current_customer=None,
        current_warehouse=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        customer_queryset = Customer.objects.filter(is_active=True)

        warehouse_queryset = Warehouse.objects.filter(is_active=True)

        if current_customer is not None:
            customer_queryset = Customer.objects.filter(
                Q(is_active=True) | Q(pk=current_customer.pk)
            )

        if current_warehouse is not None:
            warehouse_queryset = Warehouse.objects.filter(
                Q(is_active=True) | Q(pk=current_warehouse.pk)
            )

        self.fields["customer"].queryset = customer_queryset.order_by("name")

        self.fields["warehouse"].queryset = warehouse_queryset.order_by("code")


class SalesOrderItemForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True).order_by("name"),
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": "1",
                "placeholder": "1",
            }
        ),
    )

    unit_price = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0"),
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": "0",
                "step": "0.01",
                "placeholder": "0.00",
            }
        ),
    )


class BaseSalesOrderItemFormSet(BaseFormSet):
    def clean(self):
        super().clean()

        if any(self.errors):
            return

        product_ids = []
        active_items = 0

        for form in self.forms:
            cleaned_data = getattr(
                form,
                "cleaned_data",
                None,
            )

            if not cleaned_data:
                continue

            if cleaned_data.get("DELETE"):
                continue

            product = cleaned_data.get("product")

            if product is None:
                continue

            active_items += 1

            if product.pk in product_ids:
                raise forms.ValidationError(
                    "Sales order cannot contain duplicate products."
                )

            product_ids.append(product.pk)

        if active_items == 0:
            raise forms.ValidationError("Sales order must contain at least one item.")


SalesOrderItemFormSet = formset_factory(
    SalesOrderItemForm,
    formset=BaseSalesOrderItemFormSet,
    extra=1,
    can_delete=True,
)
