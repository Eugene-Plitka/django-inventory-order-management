from rest_framework.routers import DefaultRouter

from .views import (
    StockMovementViewSet,
    StockReservationViewSet,
    StockViewSet,
    WarehouseViewSet,
)


router = DefaultRouter()

router.register(
    "warehouses",
    WarehouseViewSet,
    basename="warehouse",
)

router.register(
    "stocks",
    StockViewSet,
    basename="stock",
)

router.register(
    "stock-movements",
    StockMovementViewSet,
    basename="stock-movement",
)

router.register(
    "stock-reservations",
    StockReservationViewSet,
    basename="stock-reservation",
)

urlpatterns = router.urls
