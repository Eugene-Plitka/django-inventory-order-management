from decimal import Decimal

from django import forms
from django.db.models import Q
from django.forms import BaseFormSet, formset_factory

from catalog.models import Product
from inventory.models import Warehouse
from partners.models import Supplier


class PurchaseOrderForm(forms.Form):
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.none(),
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
        current_supplier=None,
        current_warehouse=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        supplier_queryset = Supplier.objects.filter(is_active=True)

        warehouse_queryset = Warehouse.objects.filter(is_active=True)

        if current_supplier is not None:
            supplier_queryset = Supplier.objects.filter(
                Q(is_active=True) | Q(pk=current_supplier.pk)
            )

        if current_warehouse is not None:
            warehouse_queryset = Warehouse.objects.filter(
                Q(is_active=True) | Q(pk=current_warehouse.pk)
            )

        self.fields["supplier"].queryset = supplier_queryset.order_by("name")

        self.fields["warehouse"].queryset = warehouse_queryset.order_by("code")


class PurchaseOrderItemForm(forms.Form):
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


class BasePurchaseOrderItemFormSet(BaseFormSet):
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
                    "Purchase order cannot contain duplicate products."
                )

            product_ids.append(product.pk)

        if active_items == 0:
            raise forms.ValidationError(
                "Purchase order must contain at least one item."
            )


PurchaseOrderItemFormSet = formset_factory(
    PurchaseOrderItemForm,
    formset=BasePurchaseOrderItemFormSet,
    extra=1,
    can_delete=True,
)
