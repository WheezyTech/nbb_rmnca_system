from rest_framework import serializers

from .models_pnc import (
    PNCVisit,
    NewbornCareRecord,
    PNCReferral,
    PNCFollowUp,
)


class PNCVisitSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(
        source="facility.name",
        read_only=True,
    )

    pregnancy_id = serializers.CharField(
        source="pregnancy.pregnancy_id",
        read_only=True,
    )

    delivery_id = serializers.CharField(
        source="delivery.delivery_id",
        read_only=True,
    )

    class Meta:
        model = PNCVisit
        fields = "__all__"

        read_only_fields = [
            "id",
            "visit_id",
            "facility",
            "facility_name",
            "pregnancy_id",
            "delivery_id",
            "attended_by",
            "created_at",
            "updated_at",
        ]


class NewbornCareRecordSerializer(
    serializers.ModelSerializer
):
    facility_name = serializers.CharField(
        source="facility.name",
        read_only=True,
    )

    newborn_id = serializers.CharField(
        source="newborn.newborn_id",
        read_only=True,
    )

    class Meta:
        model = NewbornCareRecord
        fields = "__all__"

        read_only_fields = [
            "id",
            "record_id",
            "facility",
            "facility_name",
            "newborn_id",
            "reviewed_by",
            "created_at",
            "updated_at",
        ]


class PNCReferralSerializer(serializers.ModelSerializer):
    from_facility_name = serializers.CharField(
        source="from_facility.name",
        read_only=True,
    )

    to_facility_name = serializers.CharField(
        source="to_facility.name",
        read_only=True,
    )

    class Meta:
        model = PNCReferral
        fields = "__all__"

        read_only_fields = [
            "id",
            "referral_id",
            "from_facility",
            "from_facility_name",
            "to_facility_name",
            "referred_at",
            "accepted_at",
            "completed_at",
            "referred_by",
        ]


class PNCFollowUpSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(
        source="facility.name",
        read_only=True,
    )

    class Meta:
        model = PNCFollowUp
        fields = "__all__"

        read_only_fields = [
            "id",
            "followup_id",
            "facility",
            "facility_name",
            "completed_at",
            "completed_by",
            "created_by",
            "created_at",
            "updated_at",
        ]