from django.urls import path
from .search_views import global_search
from .web_views import (
    WebLoginView,
    WebLogoutView,
    profile,
    user_create,
    user_list,
    user_update,
)


app_name = "accounts_web"


urlpatterns = [
    path(
        "login/",
        WebLoginView.as_view(),
        name="login",
    ),
    path(
        "logout/",
        WebLogoutView.as_view(),
        name="logout",
    ),
    path(
        "profile/",
        profile,
        name="profile",
    ),
    path(
        "users/",
        user_list,
        name="user-list",
    ),
    path(
        "users/add/",
        user_create,
        name="user-create",
    ),
    path(
        "users/<int:pk>/edit/",
        user_update,
        name="user-update",
    ),
    path(
        "search/",
        global_search,
        name="global-search",
    ),
]
