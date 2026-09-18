from rest_framework import serializers

from .models import (
    RMNCAHDepartment,
    RMNCAHFacilityProfile,
    RMNCAHFacilityService,
    RMNCAHService,
    RMNCAHServiceCategory,
    RMNCAHServicePoint,
)


class RMNCAHServiceCategorySerializer(serializers.ModelSerializer):
    category_type_display = serializers.CharField(
        source="get_category_type_display",
        read_only=True,
    )

    class Meta:
        model = RMNCAHServiceCategory
        fields = [
            "id",
            "category_id",
            "code",
            "name",
            "category_type",
            "category_type_display",
            "description",
            "is_active",
            "display_order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "category_id",
            "category_type_display",
            "created_at",
            "updated_at",
        ]


class RMNCAHServiceSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    category_code = serializers.CharField(
        source="category.code",
        read_only=True,
    )

    class Meta:
        model = RMNCAHService
        fields = [
            "id",
            "service_id",
            "category",
            "category_name",
            "category_code",
            "code",
            "name",
            "description",
            "requires_clinical_staff",
            "requires_referral",
            "is_emergency_service",
            "is_active",
            "display_order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "service_id",
            "category_name",
            "category_code",
            "created_at",
            "updated_at",
        ]


class RMNCAHDepartmentSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(
        source="facility.name",
        read_only=True,
    )

    class Meta:
        model = RMNCAHDepartment
        fields = [
            "id",
            "department_id",
            "facility",
            "facility_name",
            "code",
            "name",
            "description",
            "head_name",
            "contact_phone",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "department_id",
            "facility",
            "facility_name",
            "created_at",
            "updated_at",
        ]


class RMNCAHServicePointSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(
        source="facility.name",
        read_only=True,
    )

    department_name = serializers.CharField(
        source="department.name",
        read_only=True,
    )

    point_type_display = serializers.CharField(
        source="get_point_type_display",
        read_only=True,
    )

    class Meta:
        model = RMNCAHServicePoint
        fields = [
            "id",
            "service_point_id",
            "facility",
            "facility_name",
            "department",
            "department_name",
            "code",
            "name",
            "point_type",
            "point_type_display",
            "location_description",
            "contact_phone",
            "is_24_hour",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "service_point_id",
            "facility",
            "facility_name",
            "department_name",
            "point_type_display",
            "created_at",
            "updated_at",
        ]

    def validate_department(self, department):
        facility = self.context["request"].user.facility

        if department.facility_id != facility.id:
            raise serializers.ValidationError(
                "The selected department does not belong to your facility."
            )

        return department


class RMNCAHFacilityProfileSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(
        source="facility.name",
        read_only=True,
    )

    class Meta:
        model = RMNCAHFacilityProfile
        fields = [
            "id",
            "profile_id",
            "facility",
            "facility_name",
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
            "referral_services_available",
            "ambulance_available",
            "operating_hours",
            "service_capacity_notes",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "profile_id",
            "facility",
            "facility_name",
            "created_at",
            "updated_at",
        ]


class RMNCAHFacilityServiceSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(
        source="facility.name",
        read_only=True,
    )

    service_name = serializers.CharField(
        source="service.name",
        read_only=True,
    )

    service_code = serializers.CharField(
        source="service.code",
        read_only=True,
    )

    category_name = serializers.CharField(
        source="service.category.name",
        read_only=True,
    )

    service_point_name = serializers.CharField(
        source="service_point.name",
        read_only=True,
    )

    availability_display = serializers.CharField(
        source="get_availability_display",
        read_only=True,
    )

    class Meta:
        model = RMNCAHFacilityService
        fields = [
            "id",
            "facility_service_id",
            "facility",
            "facility_name",
            "service",
            "service_name",
            "service_code",
            "category_name",
            "service_point",
            "service_point_name",
            "availability",
            "availability_display",
            "is_24_hour",
            "emergency_available",
            "referral_required",
            "minimum_staff_required",
            "current_staff_count",
            "estimated_daily_capacity",
            "operating_hours",
            "last_verified_at",
            "notes",
            "is_active",
            "configured_by",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "facility_service_id",
            "facility",
            "facility_name",
            "service_name",
            "service_code",
            "category_name",
            "service_point_name",
            "availability_display",
            "configured_by",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user

        facility = getattr(user, "facility", None)

        if facility is None:
            raise serializers.ValidationError(
                "Your user account is not assigned to a facility."
            )

        service_point = attrs.get("service_point")

        if service_point and service_point.facility_id != facility.id:
            raise serializers.ValidationError(
                {
                    "service_point": (
                        "The selected service point does not "
                        "belong to your facility."
                    )
                }
            )

        service = attrs.get("service")

        if service and not service.is_active:
            raise serializers.ValidationError(
                {
                    "service": "The selected RMNCAH service is inactive."
                }
            )

        return attrs