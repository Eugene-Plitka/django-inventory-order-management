"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import dashboard

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "",
        include("catalog.web_urls"),
    ),
    path(
        "",
        include("partners.web_urls"),
    ),
    path(
        "",
        include("inventory.web_urls"),
    ),
    path(
        "",
        include("sales.web_urls"),
    ),
    path(
        "",
        include("purchasing.web_urls"),
    ),
    path(
        "",
        include("accounts.web_urls"),
    ),
    path(
        "",
        include("notifications.urls"),
    ),
    path(
        "api/auth/login/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "api/auth/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path(
        "api/schema/",
        SpectacularAPIView.as_view(),
        name="schema",
    ),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "",
        dashboard,
        name="dashboard",
    ),
    path("api/", include("purchasing.urls")),
    path("api/", include("sales.urls")),
    path("api/", include("catalog.urls")),
    path("api/", include("partners.urls")),
    path("api/", include("inventory.urls")),
]
