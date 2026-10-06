from .models import Notification


def notifications(request):
    if not request.user.is_authenticated:
        return {
            "topbar_notifications": [],
            "unread_notifications_count": 0,
        }

    queryset = Notification.objects.filter(recipient=request.user)

    return {
        "topbar_notifications": queryset[:5],
        "unread_notifications_count": (queryset.filter(is_read=False).count()),
    }
