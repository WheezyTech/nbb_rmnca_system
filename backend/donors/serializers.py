from rest_framework import serializers

from .models import (
    Donor,
    Donation,
    DonorEligibility,
    DeferralRecord,
    BloodSample,
    LaboratoryTest,
    BloodUnit,
)


class DonorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Donor

        fields = [
            "id",
            "donor_id",
            "national_id",
            "first_name",
            "middle_name",
            "last_name",
            "date_of_birth",
            "gender",
            "phone",
            "email",
            "address",
            "emergency_contact_name",
            "emergency_contact_phone",
            "blood_group",
            "status",
            "registered_at",
            "updated_at",
            "notes",
        ]

        read_only_fields = [
            "id",
            "donor_id",
            "registered_at",
            "updated_at",
        ]


class DonationSerializer(serializers.ModelSerializer):

    donor_name = serializers.SerializerMethodField()
    facility_name = serializers.CharField(
        source="facility.name",
        read_only=True,
    )

    class Meta:
        model = Donation

        fields = [
            "id",
            "donation_id",
            "donor",
            "donor_name",
            "facility",
            "facility_name",
            "donation_type",
            "collection_date",
            "volume_ml",
            "status",
            "collection_notes",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "donation_id",
            "created_at",
            "updated_at",
        ]

    def get_donor_name(self, obj):
        return (
            f"{obj.donor.first_name} "
            f"{obj.donor.last_name}"
        )


class DonorEligibilitySerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = DonorEligibility

        fields = [
            "id",
            "donor",
            "assessment_date",
            "decision",
            "weight_kg",
            "haemoglobin",
            "blood_pressure",
            "temperature",
            "screening_notes",
            "assessed_by",
        ]

        read_only_fields = [
            "id",
            "assessment_date",
        ]


class DeferralRecordSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = DeferralRecord

        fields = [
            "id",
            "donor",
            "deferral_type",
            "reason",
            "start_date",
            "end_date",
            "recorded_by",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]


class BloodSampleSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = BloodSample

        fields = [
            "id",
            "sample_id",
            "donation",
            "collected_at",
            "received_at",
            "status",
            "collection_notes",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "sample_id",
            "created_at",
        ]


class LaboratoryTestSerializer(
    serializers.ModelSerializer
):

    def validate_sample(self, sample):

        request = self.context.get("request")

        if not request:
            return sample

        user = request.user

        if user.role in [
            "SUPER_ADMIN",
            "NATIONAL_ADMIN",
        ]:
            return sample

        if not user.facility_id:
            raise serializers.ValidationError(
                "User is not assigned to a facility."
            )

        if (
            sample.donation.facility_id
            != user.facility_id
        ):
            raise serializers.ValidationError(
                "You cannot access a sample "
                "from another facility."
            )

        return sample

    class Meta:
        model = LaboratoryTest

        fields = [
            "id",
            "test_id",
            "sample",
            "test_type",
            "status",
            "result",
            "result_notes",
            "performed_by",
            "performed_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "test_id",
            "created_at",
            "updated_at",
        ]


class BloodUnitSerializer(
    serializers.ModelSerializer
):

    facility_name = serializers.CharField(
        source="facility.name",
        read_only=True,
    )

    class Meta:
        model = BloodUnit

        fields = [
            "id",
            "unit_id",
            "donation",
            "facility",
            "facility_name",
            "blood_group",
            "component_type",
            "volume_ml",
            "collection_date",
            "expiry_date",
            "status",
            "barcode",
            "storage_location",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "unit_id",
            "barcode",
            "created_at",
            "updated_at",
        ]