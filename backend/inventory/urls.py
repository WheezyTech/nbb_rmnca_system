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
    TransfusionEventViewSet,
    TransfusionReactionViewSet,
    TransfusionReactionEventViewSet,
    TransfusionReactionInvestigationViewSet,
    HaemovigilanceReportViewSet,
    NationalHaemovigilanceViewSet,
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

router.register(
    "transfusion-reactions",
    TransfusionReactionViewSet,
    basename="transfusion-reaction",
)

router.register(
    "transfusion-reaction-events",
    TransfusionReactionEventViewSet,
    basename="transfusion-reaction-event",
)

router.register(
    "transfusion-reaction-investigations",
    TransfusionReactionInvestigationViewSet,
    basename="transfusion-reaction-investigation",
)

router.register(
    "haemovigilance-reports",
    HaemovigilanceReportViewSet,
    basename="haemovigilance-report",
)

router.register(
    "national-haemovigilance",
    NationalHaemovigilanceViewSet,
    basename="national-haemovigilance",
)

router.register(
    "transfusion-events",
    TransfusionEventViewSet,
    basename="transfusion-event",
)

urlpatterns = router.urls