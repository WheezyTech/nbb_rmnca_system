from rest_framework.routers import DefaultRouter

from .views import (
    RMNCAHDepartmentViewSet,
    RMNCAHFacilityProfileViewSet,
    RMNCAHFacilityServiceViewSet,
    RMNCAHServiceCategoryViewSet,
    RMNCAHServicePointViewSet,
    RMNCAHServiceViewSet,
)

from .views_anc import (
    ANCClientViewSet,
    PregnancyRecordViewSet,
    ANCVisitViewSet,
    ANCRiskAssessmentViewSet,
    ANCInvestigationViewSet,
    ANCReferralViewSet,
    ANCClinicalEventViewSet,
)


router = DefaultRouter()

router.register(
    "service-categories",
    RMNCAHServiceCategoryViewSet,
    basename="rmncah-service-category",
)

router.register(
    "services",
    RMNCAHServiceViewSet,
    basename="rmncah-service",
)

router.register(
    "departments",
    RMNCAHDepartmentViewSet,
    basename="rmncah-department",
)

router.register(
    "service-points",
    RMNCAHServicePointViewSet,
    basename="rmncah-service-point",
)

router.register(
    "facility-profile",
    RMNCAHFacilityProfileViewSet,
    basename="rmncah-facility-profile",
)

router.register(
    "facility-services",
    RMNCAHFacilityServiceViewSet,
    basename="rmncah-facility-service",
)

router.register(
    "anc-clients",
    ANCClientViewSet,
    basename="anc-client",
)

router.register(
    "pregnancies",
    PregnancyRecordViewSet,
    basename="pregnancy",
)

router.register(
    "anc-visits",
    ANCVisitViewSet,
    basename="anc-visit",
)

router.register(
    "anc-risk-assessments",
    ANCRiskAssessmentViewSet,
    basename="anc-risk-assessment",
)

router.register(
    "anc-investigations",
    ANCInvestigationViewSet,
    basename="anc-investigation",
)

router.register(
    "anc-referrals",
    ANCReferralViewSet,
    basename="anc-referral",
)

router.register(
    "anc-clinical-events",
    ANCClinicalEventViewSet,
    basename="anc-clinical-event",
)


urlpatterns = router.urls