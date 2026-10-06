from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user)

    status = request.GET.get(
        "status",
        "",
    ).strip()

    if status == "unread":
        notifications = notifications.filter(is_read=False)

    elif status == "read":
        notifications = notifications.filter(is_read=True)

    paginator = Paginator(
        notifications,
        20,
    )

    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "selected_status": status,
    }

    template_name = "notifications/list.html"

    if request.headers.get("HX-Request") == "true":
        template_name = "notifications/_list.html"

    return render(
        request,
        template_name,
        context,
    )


@login_required
@require_POST
def notification_open(
    request,
    pk,
):
    notification = get_object_or_404(
        Notification,
        pk=pk,
        recipient=request.user,
    )

    if not notification.is_read:
        notification.is_read = True

        notification.save(update_fields=("is_read",))

    if notification.url:
        return redirect(notification.url)

    return redirect("notifications:list")


@login_required
@require_POST
def mark_notification_read(
    request,
    pk,
):
    notification = get_object_or_404(
        Notification,
        pk=pk,
        recipient=request.user,
    )

    if not notification.is_read:
        notification.is_read = True

        notification.save(update_fields=("is_read",))

    return redirect(
        request.POST.get(
            "next",
            "/notifications/",
        )
    )


@login_required
@require_POST
def mark_all_notifications_read(
    request,
):
    Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).update(is_read=True)

    return redirect(
        request.POST.get(
            "next",
            "/notifications/",
        )
    )
