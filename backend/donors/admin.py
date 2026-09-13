from django.contrib import admin

from .models import (
    Donor,
    Donation,
    DonorEligibility,
    DeferralRecord,
    BloodSample,
    LaboratoryTest,
    BloodUnit,
)

@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):

    list_display = (
        "donor_id",
        "first_name",
        "last_name",
        "gender",
        "blood_group",
        "phone",
        "status",
        "registered_at",
    )

    search_fields = (
        "donor_id",
        "national_id",
        "first_name",
        "middle_name",
        "last_name",
        "phone",
        "email",
    )

    list_filter = (
        "gender",
        "blood_group",
        "status",
    )

    readonly_fields = (
        "donor_id",
        "registered_at",
        "updated_at",
    )


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):

    list_display = (
        "donation_id",
        "donor",
        "facility",
        "donation_type",
        "collection_date",
        "volume_ml",
        "status",
    )

    search_fields = (
        "donation_id",
        "donor__donor_id",
        "donor__first_name",
        "donor__last_name",
    )

    list_filter = (
        "donation_type",
        "status",
        "facility",
    )

    readonly_fields = (
        "donation_id",
        "created_at",
        "updated_at",
    )


@admin.register(DonorEligibility)
class DonorEligibilityAdmin(admin.ModelAdmin):

    list_display = (
        "donor",
        "assessment_date",
        "decision",
        "weight_kg",
        "haemoglobin",
        "assessed_by",
    )

    list_filter = (
        "decision",
    )

    search_fields = (
        "donor__donor_id",
        "donor__first_name",
        "donor__last_name",
    )


@admin.register(DeferralRecord)
class DeferralRecordAdmin(admin.ModelAdmin):

    list_display = (
        "donor",
        "deferral_type",
        "start_date",
        "end_date",
        "recorded_by",
    )

    list_filter = (
        "deferral_type",
    )

    search_fields = (
        "donor__donor_id",
        "donor__first_name",
        "donor__last_name",
    )

@admin.register(BloodSample)
class BloodSampleAdmin(admin.ModelAdmin):

    list_display = (
        "sample_id",
        "donation",
        "collected_at",
        "received_at",
        "status",
    )

    search_fields = (
        "sample_id",
        "donation__donation_id",
        "donation__donor__donor_id",
    )

    list_filter = (
        "status",
    )

    readonly_fields = (
        "sample_id",
        "created_at",
    )


@admin.register(LaboratoryTest)
class LaboratoryTestAdmin(admin.ModelAdmin):

    list_display = (
        "test_id",
        "sample",
        "test_type",
        "status",
        "result",
        "performed_by",
        "performed_at",
    )

    search_fields = (
        "test_id",
        "sample__sample_id",
        "sample__donation__donation_id",
    )

    list_filter = (
        "test_type",
        "status",
    )

    readonly_fields = (
        "test_id",
        "created_at",
        "updated_at",
    )


@admin.register(BloodUnit)
class BloodUnitAdmin(admin.ModelAdmin):

    list_display = (
        "unit_id",
        "barcode",
        "blood_group",
        "component_type",
        "facility",
        "collection_date",
        "expiry_date",
        "status",
        "storage_location",
    )

    search_fields = (
        "unit_id",
        "barcode",
        "blood_group",
        "donation__donation_id",
        "donation__donor__donor_id",
    )

    list_filter = (
        "blood_group",
        "component_type",
        "status",
        "facility",
    )

    readonly_fields = (
        "unit_id",
        "barcode",
        "created_at",
        "updated_at",
    )