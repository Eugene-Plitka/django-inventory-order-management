from django.urls import path

from .web_views import system_settings


app_name = "core_web"


urlpatterns = [
    path(
        "settings/",
        system_settings,
        name="settings",
    ),
]
