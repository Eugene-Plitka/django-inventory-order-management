from django.urls import path

from .views import (
    mark_all_notifications_read,
    mark_notification_read,
    notification_list,
    notification_open,
)


app_name = "notifications"


urlpatterns = [
    path(
        "notifications/",
        notification_list,
        name="list",
    ),
    path(
        "notifications/<int:pk>/open/",
        notification_open,
        name="open",
    ),
    path(
        "notifications/<int:pk>/read/",
        mark_notification_read,
        name="read",
    ),
    path(
        "notifications/read-all/",
        mark_all_notifications_read,
        name="read-all",
    ),
]
