from rest_framework import serializers

from .models_anc import (
    ANCClient,
    PregnancyRecord,
    ANCVisit,
    ANCRiskAssessment,
    ANCInvestigation,
    ANCReferral,
    ANCClinicalEvent,
)


class ANCClientSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(
        source="facility.name",
        read_only=True,
    )

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = ANCClient
        fields = [
            "id",
            "client_id",
            "facility",
            "facility_name",
            "patient_reference",
            "national_patient_number",
            "first_name",
            "middle_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "phone_number",
            "address",
            "gravida",
            "para",
            "living_children",
            "abortions",
            "stillbirths",
            "status",
            "registered_by",
            "registered_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "client_id",
            "facility",
            "facility_name",
            "full_name",
            "registered_by",
            "registered_at",
            "updated_at",
        ]

    def get_full_name(self, obj):
        return " ".join(
            part
            for part in [
                obj.first_name,
                obj.middle_name,
                obj.last_name,
            ]
            if part
        )


class PregnancyRecordSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()
    facility_name = serializers.CharField(
        source="facility.name",
        read_only=True,
    )

    class Meta:
        model = PregnancyRecord
        fields = [
            "id",
            "pregnancy_id",
            "client",
            "client_name",
            "facility",
            "facility_name",
            "last_menstrual_period",
            "expected_delivery_date",
            "pregnancy_type",
            "estimated_gestational_age_weeks",
            "gravida",
            "para",
            "high_risk",
            "risk_summary",
            "status",
            "pregnancy_outcome",
            "created_by",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "pregnancy_id",
            "facility",
            "facility_name",
            "client_name",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def get_client_name(self, obj):
        return " ".join(
            part
            for part in [
                obj.client.first_name,
                obj.client.middle_name,
                obj.client.last_name,
            ]
            if part
        )


class ANCVisitSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(
        source="facility.name",
        read_only=True,
    )

    pregnancy_id = serializers.CharField(
        source="pregnancy.pregnancy_id",
        read_only=True,
    )

    class Meta:
        model = ANCVisit
        fields = [
            "id",
            "visit_id",
            "pregnancy",
            "pregnancy_id",
            "facility",
            "facility_name",
            "visit_number",
            "visit_type",
            "visit_date",
            "gestational_age_weeks",
            "weight_kg",
            "height_cm",
            "systolic_bp",
            "diastolic_bp",
            "pulse_rate",
            "temperature_c",
            "respiratory_rate",
            "fundal_height_cm",
            "foetal_heart_rate",
            "foetal_movement_present",
            "oedema_present",
            "symptoms",
            "clinical_findings",
            "assessment",
            "plan",
            "next_visit_date",
            "status",
            "attended_by",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "visit_id",
            "pregnancy_id",
            "facility",
            "facility_name",
            "visit_number",
            "attended_by",
            "created_at",
            "updated_at",
        ]


class ANCRiskAssessmentSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(
        source="facility.name",
        read_only=True,
    )

    pregnancy_id = serializers.CharField(
        source="pregnancy.pregnancy_id",
        read_only=True,
    )

    risk_level_display = serializers.CharField(
        source="get_risk_level_display",
        read_only=True,
    )

    class Meta:
        model = ANCRiskAssessment
        fields = [
            "id",
            "assessment_id",
            "pregnancy",
            "pregnancy_id",
            "anc_visit",
            "facility",
            "facility_name",
            "risk_level",
            "risk_level_display",
            "hypertension",
            "diabetes",
            "anaemia",
            "previous_cesarean",
            "previous_postpartum_haemorrhage",
            "multiple_pregnancy",
            "previous_stillbirth",
            "previous_neonatal_death",
            "bleeding",
            "severe_headache",
            "reduced_foetal_movement",
            "other_risk_factor",
            "risk_factors",
            "clinical_action",
            "referral_required",
            "assessed_by",
            "assessed_at",
        ]

        read_only_fields = [
            "id",
            "assessment_id",
            "pregnancy_id",
            "facility",
            "facility_name",
            "assessed_by",
            "assessed_at",
        ]


class ANCInvestigationSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(
        source="facility.name",
        read_only=True,
    )

    pregnancy_id = serializers.CharField(
        source="pregnancy.pregnancy_id",
        read_only=True,
    )

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = ANCInvestigation
        fields = [
            "id",
            "investigation_id",
            "pregnancy",
            "pregnancy_id",
            "anc_visit",
            "facility",
            "facility_name",
            "test_name",
            "test_code",
            "ordered_at",
            "result",
            "result_date",
            "reference_range",
            "abnormal",
            "status",
            "status_display",
            "ordered_by",
            "notes",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "investigation_id",
            "pregnancy_id",
            "facility",
            "facility_name",
            "ordered_at",
            "ordered_by",
            "updated_at",
        ]


class ANCReferralSerializer(serializers.ModelSerializer):
    from_facility_name = serializers.CharField(
        source="from_facility.name",
        read_only=True,
    )

    to_facility_name = serializers.CharField(
        source="to_facility.name",
        read_only=True,
    )

    pregnancy_id = serializers.CharField(
        source="pregnancy.pregnancy_id",
        read_only=True,
    )

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = ANCReferral
        fields = [
            "id",
            "referral_id",
            "pregnancy",
            "pregnancy_id",
            "anc_visit",
            "from_facility",
            "from_facility_name",
            "to_facility",
            "to_facility_name",
            "reason",
            "clinical_summary",
            "urgency",
            "status",
            "status_display",
            "referral_date",
            "accepted_at",
            "completed_at",
            "referred_by",
            "notes",
        ]

        read_only_fields = [
            "id",
            "referral_id",
            "pregnancy_id",
            "from_facility",
            "from_facility_name",
            "to_facility_name",
            "referral_date",
            "accepted_at",
            "completed_at",
            "referred_by",
        ]


class ANCClinicalEventSerializer(serializers.ModelSerializer):
    pregnancy_id = serializers.CharField(
        source="pregnancy.pregnancy_id",
        read_only=True,
    )

    facility_name = serializers.CharField(
        source="facility.name",
        read_only=True,
    )

    event_type_display = serializers.CharField(
        source="get_event_type_display",
        read_only=True,
    )

    performed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ANCClinicalEvent
        fields = [
            "id",
            "event_id",
            "pregnancy",
            "pregnancy_id",
            "facility",
            "facility_name",
            "event_type",
            "event_type_display",
            "description",
            "metadata",
            "performed_by",
            "performed_by_name",
            "created_at",
        ]

        read_only_fields = fields

    def get_performed_by_name(self, obj):
        return (
            obj.performed_by.get_full_name()
            or obj.performed_by.username
        )