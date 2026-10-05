from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    ManufacturerViewSet,
    ProductViewSet,
)

router = DefaultRouter()

router.register(
    "categories",
    CategoryViewSet,
    basename="category",
)

router.register(
    "manufacturers",
    ManufacturerViewSet,
    basename="manufacturer",
)

router.register(
    "products",
    ProductViewSet,
    basename="product",
)

urlpatterns = router.urls
