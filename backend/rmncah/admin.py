from django.contrib import admin

from .models_anc import (
    ANCClient,
    PregnancyRecord,
    ANCVisit,
    ANCRiskAssessment,
    ANCInvestigation,
    ANCReferral,
    ANCClinicalEvent,
)


from .models import (
    RMNCAHDepartment,
    RMNCAHFacilityProfile,
    RMNCAHFacilityService,
    RMNCAHService,
    RMNCAHServiceCategory,
    RMNCAHServicePoint,
)


@admin.register(RMNCAHServiceCategory)
class RMNCAHServiceCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "category_id",
        "code",
        "name",
        "category_type",
        "is_active",
        "display_order",
    )

    list_filter = (
        "category_type",
        "is_active",
    )

    search_fields = (
        "category_id",
        "code",
        "name",
    )

    ordering = (
        "display_order",
        "name",
    )

    readonly_fields = (
        "category_id",
        "created_at",
        "updated_at",
    )


@admin.register(RMNCAHService)
class RMNCAHServiceAdmin(admin.ModelAdmin):
    list_display = (
        "service_id",
        "code",
        "name",
        "category",
        "requires_clinical_staff",
        "is_emergency_service",
        "is_active",
    )

    list_filter = (
        "category",
        "requires_clinical_staff",
        "requires_referral",
        "is_emergency_service",
        "is_active",
    )

    search_fields = (
        "service_id",
        "code",
        "name",
        "description",
    )

    ordering = (
        "category",
        "display_order",
        "name",
    )

    readonly_fields = (
        "service_id",
        "created_at",
        "updated_at",
    )


@admin.register(RMNCAHDepartment)
class RMNCAHDepartmentAdmin(admin.ModelAdmin):
    list_display = (
        "department_id",
        "facility",
        "code",
        "name",
        "head_name",
        "is_active",
    )

    list_filter = (
        "facility",
        "is_active",
    )

    search_fields = (
        "department_id",
        "code",
        "name",
        "facility__name",
        "head_name",
    )

    readonly_fields = (
        "department_id",
        "created_at",
        "updated_at",
    )


@admin.register(RMNCAHServicePoint)
class RMNCAHServicePointAdmin(admin.ModelAdmin):
    list_display = (
        "service_point_id",
        "facility",
        "department",
        "code",
        "name",
        "point_type",
        "is_24_hour",
        "is_active",
    )

    list_filter = (
        "facility",
        "point_type",
        "is_24_hour",
        "is_active",
    )

    search_fields = (
        "service_point_id",
        "code",
        "name",
        "facility__name",
    )

    readonly_fields = (
        "service_point_id",
        "created_at",
        "updated_at",
    )


@admin.register(RMNCAHFacilityProfile)
class RMNCAHFacilityProfileAdmin(admin.ModelAdmin):
    list_display = (
        "profile_id",
        "facility",
        "rmncah_enabled",
        "maternal_services_available",
        "newborn_services_available",
        "child_health_services_available",
        "emergency_obstetric_care",
        "blood_transfusion_available",
        "is_active",
    )

    list_filter = (
        "rmncah_enabled",
        "maternal_services_available",
        "newborn_services_available",
        "child_health_services_available",
        "adolescent_services_available",
        "family_planning_available",
        "reproductive_health_available",
        "emergency_obstetric_care",
        "newborn_emergency_care",
        "caesarean_section_available",
        "blood_transfusion_available",
        "ambulance_available",
        "is_active",
    )

    search_fields = (
        "profile_id",
        "facility__name",
    )

    readonly_fields = (
        "profile_id",
        "created_at",
        "updated_at",
    )


@admin.register(RMNCAHFacilityService)
class RMNCAHFacilityServiceAdmin(admin.ModelAdmin):
    list_display = (
        "facility_service_id",
        "facility",
        "service",
        "availability",
        "is_24_hour",
        "emergency_available",
        "current_staff_count",
        "estimated_daily_capacity",
        "is_active",
    )

    list_filter = (
        "facility",
        "availability",
        "is_24_hour",
        "emergency_available",
        "referral_required",
        "is_active",
    )

    search_fields = (
        "facility_service_id",
        "facility__name",
        "service__name",
        "service__code",
    )

    readonly_fields = (
        "facility_service_id",
        "created_at",
        "updated_at",
    )

@admin.register(ANCClient)
class ANCClientAdmin(admin.ModelAdmin):
    list_display = (
        "client_id",
        "patient_reference",
        "first_name",
        "last_name",
        "facility",
        "status",
        "registered_at",
    )

    list_filter = (
        "facility",
        "status",
    )

    search_fields = (
        "client_id",
        "patient_reference",
        "national_patient_number",
        "first_name",
        "middle_name",
        "last_name",
        "phone_number",
    )

    readonly_fields = (
        "client_id",
        "registered_at",
        "updated_at",
    )


@admin.register(PregnancyRecord)
class PregnancyRecordAdmin(admin.ModelAdmin):
    list_display = (
        "pregnancy_id",
        "client",
        "facility",
        "pregnancy_type",
        "high_risk",
        "status",
        "expected_delivery_date",
    )

    list_filter = (
        "facility",
        "pregnancy_type",
        "high_risk",
        "status",
    )

    search_fields = (
        "pregnancy_id",
        "client__patient_reference",
        "client__first_name",
        "client__last_name",
    )

    readonly_fields = (
        "pregnancy_id",
        "created_at",
        "updated_at",
    )


@admin.register(ANCVisit)
class ANCVisitAdmin(admin.ModelAdmin):
    list_display = (
        "visit_id",
        "pregnancy",
        "facility",
        "visit_number",
        "visit_type",
        "visit_date",
        "status",
    )

    list_filter = (
        "facility",
        "visit_type",
        "status",
    )

    search_fields = (
        "visit_id",
        "pregnancy__pregnancy_id",
    )

    readonly_fields = (
        "visit_id",
        "created_at",
        "updated_at",
    )


@admin.register(ANCRiskAssessment)
class ANCRiskAssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "assessment_id",
        "pregnancy",
        "facility",
        "risk_level",
        "referral_required",
        "assessed_at",
    )

    list_filter = (
        "facility",
        "risk_level",
        "referral_required",
        "hypertension",
        "diabetes",
        "anaemia",
    )

    search_fields = (
        "assessment_id",
        "pregnancy__pregnancy_id",
    )

    readonly_fields = (
        "assessment_id",
        "assessed_at",
    )


@admin.register(ANCInvestigation)
class ANCInvestigationAdmin(admin.ModelAdmin):
    list_display = (
        "investigation_id",
        "pregnancy",
        "facility",
        "test_name",
        "status",
        "abnormal",
        "ordered_at",
    )

    list_filter = (
        "facility",
        "status",
        "abnormal",
    )

    search_fields = (
        "investigation_id",
        "test_name",
        "test_code",
        "pregnancy__pregnancy_id",
    )

    readonly_fields = (
        "investigation_id",
        "ordered_at",
        "updated_at",
    )


@admin.register(ANCReferral)
class ANCReferralAdmin(admin.ModelAdmin):
    list_display = (
        "referral_id",
        "pregnancy",
        "from_facility",
        "to_facility",
        "urgency",
        "status",
        "referral_date",
    )

    list_filter = (
        "urgency",
        "status",
        "from_facility",
        "to_facility",
    )

    search_fields = (
        "referral_id",
        "pregnancy__pregnancy_id",
        "reason",
    )

    readonly_fields = (
        "referral_id",
        "referral_date",
        "accepted_at",
        "completed_at",
    )


@admin.register(ANCClinicalEvent)
class ANCClinicalEventAdmin(admin.ModelAdmin):
    list_display = (
        "event_id",
        "pregnancy",
        "facility",
        "event_type",
        "performed_by",
        "created_at",
    )

    list_filter = (
        "facility",
        "event_type",
    )

    search_fields = (
        "event_id",
        "pregnancy__pregnancy_id",
        "description",
    )

    readonly_fields = (
        "event_id",
        "created_at",
    )