from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


ROLE_PERMISSIONS = {
    "Administrator": {
        "accounts": {
            "user": {"view", "add", "change"},
        },
        "catalog": {
            "category": {"view", "add", "change"},
            "manufacturer": {"view", "add", "change"},
            "product": {"view", "add", "change"},
        },
        "partners": {
            "customer": {"view", "add", "change"},
            "supplier": {"view", "add", "change"},
        },
        "inventory": {
            "warehouse": {"view", "add", "change"},
            "stock": {"view"},
            "stockreservation": {"view"},
            "stockmovement": {"view"},
        },
        "sales": {
            "salesorder": {"view", "add", "change"},
            "salesorderitem": {"view", "add", "change"},
        },
        "purchasing": {
            "purchaseorder": {"view", "add", "change"},
            "purchaseorderitem": {"view", "add", "change"},
        },
    },
    "Sales Manager": {
        "catalog": {
            "category": {"view"},
            "manufacturer": {"view"},
            "product": {"view"},
        },
        "partners": {
            "customer": {"view", "add", "change"},
        },
        "inventory": {
            "warehouse": {"view"},
            "stock": {"view"},
        },
        "sales": {
            "salesorder": {"view", "add", "change"},
            "salesorderitem": {"view", "add", "change"},
        },
    },
    "Purchasing Manager": {
        "catalog": {
            "category": {"view"},
            "manufacturer": {"view"},
            "product": {"view"},
        },
        "partners": {
            "supplier": {"view", "add", "change"},
        },
        "inventory": {
            "warehouse": {"view"},
            "stock": {"view"},
        },
        "purchasing": {
            "purchaseorder": {"view", "add", "change"},
            "purchaseorderitem": {"view", "add", "change"},
        },
    },
    "Warehouse Employee": {
        "catalog": {
            "category": {"view"},
            "manufacturer": {"view"},
            "product": {"view"},
        },
        "inventory": {
            "warehouse": {"view"},
            "stock": {"view"},
            "stockmovement": {"view"},
        },
        "sales": {
            "salesorder": {"view"},
            "salesorderitem": {"view"},
        },
        "purchasing": {
            "purchaseorder": {"view"},
            "purchaseorderitem": {"view"},
        },
    },
}


class Command(BaseCommand):
    help = "Create project roles and assign Django model permissions."

    def handle(self, *args, **options):
        for role_name, apps_permissions in ROLE_PERMISSIONS.items():
            group, created = Group.objects.get_or_create(name=role_name)

            permissions = []

            for app_label, models_permissions in apps_permissions.items():
                for model_name, actions in models_permissions.items():
                    codenames = [f"{action}_{model_name}" for action in actions]

                    model_permissions = Permission.objects.filter(
                        content_type__app_label=app_label,
                        content_type__model=model_name,
                        codename__in=codenames,
                    )

                    permissions.extend(model_permissions)

            group.permissions.set(permissions)

            action = "Created" if created else "Updated"

            self.stdout.write(self.style.SUCCESS(f"{action} role: {role_name}"))
