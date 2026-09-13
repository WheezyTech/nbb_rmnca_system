from rest_framework.routers import DefaultRouter

from .views import (
    DonorViewSet,
    DonationViewSet,
    DonorEligibilityViewSet,
    DeferralRecordViewSet,
    BloodSampleViewSet,
    LaboratoryTestViewSet,
    BloodUnitViewSet,
)


router = DefaultRouter()

router.register(
    "donors",
    DonorViewSet,
    basename="donor",
)

router.register(
    "donations",
    DonationViewSet,
    basename="donation",
)

router.register(
    "eligibility",
    DonorEligibilityViewSet,
    basename="donor-eligibility",
)

router.register(
    "deferrals",
    DeferralRecordViewSet,
    basename="deferral",
)

router.register(
    "samples",
    BloodSampleViewSet,
    basename="blood-sample",
)

router.register(
    "laboratory-tests",
    LaboratoryTestViewSet,
    basename="laboratory-test",
)

router.register(
    "blood-units",
    BloodUnitViewSet,
    basename="blood-unit",
)


urlpatterns = router.urls