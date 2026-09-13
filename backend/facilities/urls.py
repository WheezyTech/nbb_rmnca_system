from rest_framework.routers import DefaultRouter
from .views import (
    RegionViewSet,
    CountyViewSet,
    FacilityViewSet,
)


router = DefaultRouter()

router.register(
    "regions",
    RegionViewSet,
    basename="region",
)

router.register(
    "counties",
    CountyViewSet,
    basename="county",
)

router.register(
    "facilities",
    FacilityViewSet,
    basename="facility",
)

urlpatterns = router.urls