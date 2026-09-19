from rest_framework import serializers

from .models_delivery import (
    DeliveryRecord,
    NewbornRecord,
    LabourRecord,
    PostnatalMotherRecord,
)


class DeliveryRecordSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(
        source="facility.name",
        read_only=True,
    )
    pregnancy_id = serializers.CharField(
        source="pregnancy.pregnancy_id",
        read_only=True,
    )
    attended_by_name = serializers.SerializerMethodField()

    class Meta:
        model = DeliveryRecord
        fields = [
            "id",
            "delivery_id",
            "pregnancy",
            "pregnancy_id",
            "facility",
            "facility_name",
            "delivery_date",
            "delivery_mode",
            "delivery_status",
            "gestational_age_weeks",
            "number_of_babies",
            "attended_by",
            "attended_by_name",
            "indication_for_caesarean",
            "complications",
            "estimated_blood_loss_ml",
            "placenta_complete",
            "maternal_condition",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "delivery_id",
            "facility",
            "facility_name",
            "pregnancy_id",
            "attended_by",
            "attended_by_name",
            "created_at",
            "updated_at",
        ]

    def get_attended_by_name(self, obj):
        return (
            obj.attended_by.get_full_name()
            or obj.attended_by.username
        )


class NewbornRecordSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(
        source="facility.name",
        read_only=True,
    )
    delivery_id = serializers.CharField(
        source="delivery.delivery_id",
        read_only=True,
    )
    newborn_status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = NewbornRecord
        fields = [
            "id",
            "newborn_id",
            "delivery",
            "delivery_id",
            "pregnancy",
            "facility",
            "facility_name",
            "birth_order",
            "sex",
            "date_time_of_birth",
            "birth_weight_kg",
            "length_cm",
            "head_circumference_cm",
            "apgar_one_minute",
            "apgar_five_minutes",
            "apgar_ten_minutes",
            "condition",
            "status",
            "newborn_status_display",
            "resuscitation_required",
            "resuscitation_details",
            "immediate_care",
            "transferred_to_nicu",
            "nicu_reason",
            "complications",
            "notes",
            "recorded_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "newborn_id",
            "facility",
            "facility_name",
            "delivery_id",
            "recorded_by",
            "created_at",
            "updated_at",
        ]


class LabourRecordSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(
        source="facility.name",
        read_only=True,
    )
    pregnancy_id = serializers.CharField(
        source="pregnancy.pregnancy_id",
        read_only=True,
    )

    class Meta:
        model = LabourRecord
        fields = [
            "id",
            "labour_id",
            "pregnancy",
            "pregnancy_id",
            "facility",
            "facility_name",
            "admission_date",
            "labour_onset_date",
            "cervical_dilation_cm",
            "contractions_per_10_minutes",
            "membrane_status",
            "liquor_character",
            "fetal_presentation",
            "fetal_position",
            "fetal_heart_rate",
            "maternal_bp_systolic",
            "maternal_bp_diastolic",
            "maternal_pulse",
            "maternal_temperature",
            "status",
            "complications",
            "management_plan",
            "notes",
            "managed_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "labour_id",
            "facility",
            "facility_name",
            "pregnancy_id",
            "managed_by",
            "created_at",
            "updated_at",
        ]


class PostnatalMotherRecordSerializer(
    serializers.ModelSerializer
):
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
        model = PostnatalMotherRecord
        fields = [
            "id",
            "postnatal_id",
            "pregnancy",
            "pregnancy_id",
            "delivery",
            "delivery_id",
            "facility",
            "facility_name",
            "assessment_date",
            "days_after_delivery",
            "temperature_c",
            "systolic_bp",
            "diastolic_bp",
            "pulse_rate",
            "bleeding",
            "fever",
            "breast_condition",
            "uterine_involution",
            "lochia",
            "wound_condition",
            "mental_health_observation",
            "breastfeeding_status",
            "complications",
            "clinical_assessment",
            "plan",
            "status",
            "reviewed_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "postnatal_id",
            "facility",
            "facility_name",
            "pregnancy_id",
            "delivery_id",
            "reviewed_by",
            "created_at",
            "updated_at",
        ]