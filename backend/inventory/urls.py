from rest_framework.routers import DefaultRouter

from .views import (
    StorageLocationViewSet,
    InventoryRecordViewSet,
    BloodReservationViewSet,
    BloodIssueViewSet,
    BloodTransferViewSet,
    InventoryMovementViewSet,
    InventoryShortageViewSet,
    BloodStockAlertViewSet,
    BloodRequestViewSet,
)


router = DefaultRouter()


router.register(
    "storage-locations",
    StorageLocationViewSet,
    basename="storage-location",
)


router.register(
    "stock",
    InventoryRecordViewSet,
    basename="inventory-stock",
)


router.register(
    "reservations",
    BloodReservationViewSet,
    basename="blood-reservation",
)


router.register(
    "issues",
    BloodIssueViewSet,
    basename="blood-issue",
)


router.register(
    "transfers",
    BloodTransferViewSet,
    basename="blood-transfer",
)


router.register(
    "movements",
    InventoryMovementViewSet,
    basename="inventory-movement",
)


router.register(
    "alerts",
    InventoryShortageViewSet,
    basename="inventory-alerts",
)

router.register(
    "alerts",
    BloodStockAlertViewSet,
    basename="blood-stock-alert",
)

router.register(
    "blood-requests",
    BloodRequestViewSet,
    basename="blood-request",
)

urlpatterns = router.urls