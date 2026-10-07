from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from .forms import SystemSettingsForm
from .models import SystemSettings


def _is_administrator(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name="Administrator").exists()
    )


@login_required
def system_settings(request):
    if not _is_administrator(request.user):
        raise PermissionDenied

    settings_object = SystemSettings.load()

    if request.method == "POST":
        form = SystemSettingsForm(
            request.POST,
            instance=settings_object,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "System settings updated successfully.",
            )

            return redirect("core_web:settings")

    else:
        form = SystemSettingsForm(instance=settings_object)

    return render(
        request,
        "core/settings.html",
        {
            "form": form,
        },
    )
