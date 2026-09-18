from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    RMNCAHDepartment,
    RMNCAHFacilityProfile,
    RMNCAHFacilityService,
    RMNCAHService,
    RMNCAHServiceCategory,
    RMNCAHServicePoint,
)

from .serializers import (
    RMNCAHDepartmentSerializer,
    RMNCAHFacilityProfileSerializer,
    RMNCAHFacilityServiceSerializer,
    RMNCAHServiceSerializer,
    RMNCAHServiceCategorySerializer,
    RMNCAHServicePointSerializer,
)


class RMNCAHScopedMixin:
    """
    Facility-level data isolation.

    National administrators can see all facilities.
    Regional/county administration can be expanded later
    using the existing facility hierarchy.
    """

    NATIONAL_ROLES = {
        "SUPER_ADMIN",
        "NATIONAL_ADMIN",
    }

    def scoped_queryset(self, queryset):
        user = self.request.user

        if user.role in self.NATIONAL_ROLES:
            return queryset

        if not user.facility_id:
            return queryset.none()

        if "facility" in [field.name for field in queryset.model._meta.fields]:
            return queryset.filter(facility_id=user.facility_id)

        if queryset.model is RMNCAHServicePoint:
            return queryset.filter(facility_id=user.facility_id)

        if queryset.model is RMNCAHDepartment:
            return queryset.filter(facility_id=user.facility_id)

        if queryset.model is RMNCAHFacilityProfile:
            return queryset.filter(facility_id=user.facility_id)

        if queryset.model is RMNCAHFacilityService:
            return queryset.filter(facility_id=user.facility_id)

        return queryset


class RMNCAHServiceCategoryViewSet(
    RMNCAHScopedMixin,
    viewsets.ModelViewSet,
):
    queryset = RMNCAHServiceCategory.objects.all()
    serializer_class = RMNCAHServiceCategorySerializer
    permission_classes = [IsAuthenticated]

    http_method_names = [
        "get",
        "post",
        "patch",
        "head",
        "options",
    ]

    def get_queryset(self):
        queryset = self.queryset

        active = self.request.query_params.get("is_active")

        if active is not None:
            queryset = queryset.filter(
                is_active=active.lower() == "true"
            )

        category_type = self.request.query_params.get("category_type")

        if category_type:
            queryset = queryset.filter(
                category_type=category_type.upper()
            )

        return queryset.order_by("display_order", "name")


class RMNCAHServiceViewSet(
    RMNCAHScopedMixin,
    viewsets.ModelViewSet,
):
    queryset = RMNCAHService.objects.select_related(
        "category"
    ).all()

    serializer_class = RMNCAHServiceSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = [
        "get",
        "post",
        "patch",
        "head",
        "options",
    ]

    def get_queryset(self):
        queryset = self.queryset

        active = self.request.query_params.get("is_active")

        if active is not None:
            queryset = queryset.filter(
                is_active=active.lower() == "true"
            )

        category = self.request.query_params.get("category")

        if category:
            queryset = queryset.filter(
                category_id=category
            )

        category_type = self.request.query_params.get("category_type")

        if category_type:
            queryset = queryset.filter(
                category__category_type=category_type.upper()
            )

        return queryset.order_by(
            "category__display_order",
            "display_order",
            "name",
        )


class RMNCAHDepartmentViewSet(
    RMNCAHScopedMixin,
    viewsets.ModelViewSet,
):
    queryset = RMNCAHDepartment.objects.select_related(
        "facility"
    ).all()

    serializer_class = RMNCAHDepartmentSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = [
        "get",
        "post",
        "patch",
        "head",
        "options",
    ]

    def get_queryset(self):
        queryset = self.scoped_queryset(self.queryset)

        active = self.request.query_params.get("is_active")

        if active is not None:
            queryset = queryset.filter(
                is_active=active.lower() == "true"
            )

        return queryset.order_by("name")

    def perform_create(self, serializer):
        user = self.request.user

        if not user.facility_id:
            raise PermissionDenied(
                "Your user account is not assigned to a facility."
            )

        serializer.save(facility=user.facility)


class RMNCAHServicePointViewSet(
    RMNCAHScopedMixin,
    viewsets.ModelViewSet,
):
    queryset = RMNCAHServicePoint.objects.select_related(
        "facility",
        "department",
    ).all()

    serializer_class = RMNCAHServicePointSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = [
        "get",
        "post",
        "patch",
        "head",
        "options",
    ]

    def get_queryset(self):
        queryset = self.scoped_queryset(self.queryset)

        active = self.request.query_params.get("is_active")

        if active is not None:
            queryset = queryset.filter(
                is_active=active.lower() == "true"
            )

        point_type = self.request.query_params.get("point_type")

        if point_type:
            queryset = queryset.filter(
                point_type=point_type.upper()
            )

        department = self.request.query_params.get("department")

        if department:
            queryset = queryset.filter(
                department_id=department
            )

        return queryset.order_by("name")

    def perform_create(self, serializer):
        user = self.request.user

        if not user.facility_id:
            raise PermissionDenied(
                "Your user account is not assigned to a facility."
            )

        serializer.save(facility=user.facility)


class RMNCAHFacilityProfileViewSet(
    RMNCAHScopedMixin,
    viewsets.ModelViewSet,
):
    queryset = RMNCAHFacilityProfile.objects.select_related(
        "facility"
    ).all()

    serializer_class = RMNCAHFacilityProfileSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = [
        "get",
        "post",
        "patch",
        "head",
        "options",
    ]

    def get_queryset(self):
        return self.scoped_queryset(self.queryset)

    def perform_create(self, serializer):
        user = self.request.user

        if not user.facility_id:
            raise PermissionDenied(
                "Your user account is not assigned to a facility."
            )

        if RMNCAHFacilityProfile.objects.filter(
            facility_id=user.facility_id
        ).exists():
            raise DjangoValidationError(
                "An RMNCAH facility profile already exists for this facility."
            )

        serializer.save(
            facility=user.facility,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="my-facility",
    )
    def my_facility(self, request):
        user = request.user

        if not user.facility_id:
            raise PermissionDenied(
                "Your user account is not assigned to a facility."
            )

        profile = RMNCAHFacilityProfile.objects.filter(
            facility_id=user.facility_id
        ).first()

        if not profile:
            return Response(
                {
                    "detail": (
                        "No RMNCAH profile has been configured "
                        "for your facility."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(profile)

        return Response(serializer.data)


class RMNCAHFacilityServiceViewSet(
    RMNCAHScopedMixin,
    viewsets.ModelViewSet,
):
    queryset = RMNCAHFacilityService.objects.select_related(
        "facility",
        "service",
        "service__category",
        "service_point",
        "configured_by",
    ).all()

    serializer_class = RMNCAHFacilityServiceSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = [
        "get",
        "post",
        "patch",
        "head",
        "options",
    ]

    def get_queryset(self):
        queryset = self.scoped_queryset(self.queryset)

        availability = self.request.query_params.get(
            "availability"
        )

        if availability:
            queryset = queryset.filter(
                availability=availability.upper()
            )

        service = self.request.query_params.get("service")

        if service:
            queryset = queryset.filter(
                service_id=service
            )

        category = self.request.query_params.get("category")

        if category:
            queryset = queryset.filter(
                service__category_id=category
            )

        emergency = self.request.query_params.get(
            "emergency_available"
        )

        if emergency is not None:
            queryset = queryset.filter(
                emergency_available=emergency.lower() == "true"
            )

        return queryset.order_by(
            "service__category__display_order",
            "service__display_order",
            "service__name",
        )

    def perform_create(self, serializer):
        user = self.request.user

        if not user.facility_id:
            raise PermissionDenied(
                "Your user account is not assigned to a facility."
            )

        service_point = serializer.validated_data.get(
            "service_point"
        )

        if (
            service_point
            and service_point.facility_id != user.facility_id
        ):
            raise PermissionDenied(
                "The selected service point does not belong "
                "to your facility."
            )

        serializer.save(
            facility=user.facility,
            configured_by=user,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="available",
    )
    def available(self, request):
        queryset = self.get_queryset().filter(
            availability=RMNCAHFacilityService.Availability.AVAILABLE,
            is_active=True,
        )

        serializer = self.get_serializer(
            queryset,
            many=True,
        )

        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path="emergency",
    )
    def emergency(self, request):
        queryset = self.get_queryset().filter(
            emergency_available=True,
            is_active=True,
        )

        serializer = self.get_serializer(
            queryset,
            many=True,
        )

        return Response(serializer.data)

