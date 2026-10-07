from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from core.pagination import get_items_per_page

from .models import Notification


def _safe_next_url(request):
    next_url = request.POST.get(
        "next",
        "",
    )

    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url

    return "/notifications/"


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user)

    status = request.GET.get(
        "status",
        "",
    ).strip()

    sort = request.GET.get(
        "sort",
        "newest",
    ).strip()

    if status == "unread":
        notifications = notifications.filter(is_read=False)

    elif status == "read":
        notifications = notifications.filter(is_read=True)

    sort_fields = {
        "newest": "-created_at",
        "oldest": "created_at",
    }

    order_by = sort_fields.get(
        sort,
        "-created_at",
    )

    if sort not in sort_fields:
        sort = "newest"

    notifications = notifications.order_by(
        order_by,
        "-id",
    )

    paginator = Paginator(
        notifications,
        get_items_per_page(),
    )

    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "selected_status": status,
        "sort": sort,
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

    return redirect(_safe_next_url(request))


@login_required
@require_POST
def mark_all_notifications_read(
    request,
):
    Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).update(is_read=True)

    return redirect(_safe_next_url(request))
