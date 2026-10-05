from typing import ClassVar

from rest_framework.permissions import BasePermission, DjangoModelPermissions


class StrictDjangoModelPermissions(DjangoModelPermissions):
    perms_map: ClassVar[dict[str, list[str]]] = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": [],
        "HEAD": [],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }


class HasAnyRole(BasePermission):
    allowed_roles: ClassVar[set[str]] = set()

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        return request.user.groups.filter(
            name__in=self.allowed_roles,
        ).exists()


class CanManageSalesOrder(HasAnyRole):
    allowed_roles: ClassVar[set[str]] = {
        "Administrator",
        "Sales Manager",
    }


class CanProcessSalesOrder(HasAnyRole):
    allowed_roles: ClassVar[set[str]] = {
        "Administrator",
        "Warehouse Employee",
    }


class CanManagePurchaseOrder(HasAnyRole):
    allowed_roles: ClassVar[set[str]] = {
        "Administrator",
        "Purchasing Manager",
    }


class CanReceivePurchaseOrder(HasAnyRole):
    allowed_roles: ClassVar[set[str]] = {
        "Administrator",
        "Warehouse Employee",
    }
