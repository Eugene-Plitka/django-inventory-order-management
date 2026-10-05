from django.core.management.base import BaseCommand

from accounts.services import setup_roles


class Command(BaseCommand):
    help = "Create project roles and assign Django model permissions."

    def handle(self, *args, **options):
        results = setup_roles()

        for role_name, created in results:
            action = "Created" if created else "Updated"

            self.stdout.write(self.style.SUCCESS(f"{action} role: {role_name}"))
