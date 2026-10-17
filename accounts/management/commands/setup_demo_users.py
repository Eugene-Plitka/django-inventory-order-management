import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


DEMO_USERS = (
    {
        "email": "admin@demo.example.com",
        "first_name": "Demo",
        "last_name": "Administrator",
        "role": "Administrator",
    },
    {
        "email": "sales@demo.example.com",
        "first_name": "Demo",
        "last_name": "Sales",
        "role": "Sales Manager",
    },
    {
        "email": "purchasing@demo.example.com",
        "first_name": "Demo",
        "last_name": "Purchasing",
        "role": "Purchasing Manager",
    },
    {
        "email": "warehouse@demo.example.com",
        "first_name": "Demo",
        "last_name": "Warehouse",
        "role": "Warehouse Employee",
    },
)


class Command(BaseCommand):
    help = "Create or restore demo users and their roles."

    def handle(self, *args, **options):
        password = os.environ.get("DEMO_USER_PASSWORD")

        if not password or len(password) < 12:
            raise CommandError("DEMO_USER_PASSWORD must be at least 12 characters.")

        User = get_user_model()

        with transaction.atomic():
            for data in DEMO_USERS:
                try:
                    role = Group.objects.get(name=data["role"])
                except Group.DoesNotExist as exc:
                    raise CommandError(
                        f"Missing role: {data['role']}. Run setup_roles first."
                    ) from exc

                user, created = User.objects.get_or_create(
                    email=data["email"],
                )

                user.first_name = data["first_name"]
                user.last_name = data["last_name"]
                user.is_active = True
                user.is_staff = False
                user.is_superuser = False
                user.set_password(password)
                user.save()

                user.groups.set([role])
                user.user_permissions.clear()

                action = "Created" if created else "Restored"

                self.stdout.write(
                    self.style.SUCCESS(f"{action}: {user.email} ({role.name})")
                )
