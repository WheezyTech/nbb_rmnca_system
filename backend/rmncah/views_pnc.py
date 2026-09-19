from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from .models_pnc import (
    PNCVisit,
    NewbornCareRecord,
    PNCReferral,
    PNCFollowUp,
)

from .serializers_pnc import (
    PNCVisitSerializer,
    NewbornCareRecordSerializer,
    PNCReferralSerializer,
    PNCFollowUpSerializer,
)

from .services_pnc import (
    create_pnc_visit,
    create_newborn_care_record,
    create_pnc_referral,
    create_pnc_followup,
    complete_pnc_followup,
)


class PNCScopedMixin:

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

        return queryset.filter(
            facility_id=user.facility_id
        )


class PNCVisitViewSet(
    PNCScopedMixin,
    viewsets.ModelViewSet,
):
    queryset = PNCVisit.objects.select_related(
        "pregnancy",
        "delivery",
        "facility",
        "attended_by",
    ).all()

    serializer_class = PNCVisitSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = [
        "get",
        "post",
        "patch",
        "head",
        "options",
    ]

    def get_queryset(self):
        queryset = self.scoped_queryset(
            self.queryset
        )

        pregnancy = self.request.query_params.get(
            "pregnancy"
        )

        if pregnancy:
            queryset = queryset.filter(
                pregnancy_id=pregnancy
            )

        return queryset

    def create(self, request, *args, **kwargs):
        user = request.user

        if not user.facility_id:
            raise PermissionDenied(
                "Your user account is not assigned to a facility."
            )

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        pregnancy = serializer.validated_data["pregnancy"]
        delivery = serializer.validated_data["delivery"]

        if pregnancy.facility_id != user.facility_id:
            raise PermissionDenied(
                "The pregnancy does not belong to your facility."
            )

        try:
            visit = create_pnc_visit(
                pregnancy=pregnancy,
                delivery=delivery,
                attended_by=user,
                **{
                    key: value
                    for key, value in serializer.validated_data.items()
                    if key not in ["pregnancy", "delivery"]
                },
            )
        except DjangoValidationError as exc:
            raise PermissionDenied(str(exc))

        return Response(
            self.get_serializer(visit).data,
            status=status.HTTP_201_CREATED,
        )


class NewbornCareRecordViewSet(
    PNCScopedMixin,
    viewsets.ModelViewSet,
):
    queryset = NewbornCareRecord.objects.select_related(
        "newborn",
        "pregnancy",
        "delivery",
        "facility",
        "reviewed_by",
    ).all()

    serializer_class = NewbornCareRecordSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = [
        "get",
        "post",
        "patch",
        "head",
        "options",
    ]

    def get_queryset(self):
        queryset = self.scoped_queryset(
            self.queryset
        )

        newborn = self.request.query_params.get(
            "newborn"
        )

        if newborn:
            queryset = queryset.filter(
                newborn_id=newborn
            )

        return queryset

    def create(self, request, *args, **kwargs):
        user = request.user

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        newborn = serializer.validated_data["newborn"]

        if newborn.facility_id != user.facility_id:
            raise PermissionDenied(
                "The newborn does not belong to your facility."
            )

        record = create_newborn_care_record(
            newborn=newborn,
            reviewed_by=user,
            **{
                key: value
                for key, value in serializer.validated_data.items()
                if key != "newborn"
            },
        )

        return Response(
            self.get_serializer(record).data,
            status=status.HTTP_201_CREATED,
        )


class PNCReferralViewSet(
    PNCScopedMixin,
    viewsets.ModelViewSet,
):
    queryset = PNCReferral.objects.select_related(
        "pregnancy",
        "newborn",
        "from_facility",
        "to_facility",
        "referred_by",
    ).all()

    serializer_class = PNCReferralSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = [
        "get",
        "post",
        "patch",
        "head",
        "options",
    ]

    def get_queryset(self):
        queryset = self.scoped_queryset(
            self.queryset
        )

        referral_status = self.request.query_params.get(
            "status"
        )

        if referral_status:
            queryset = queryset.filter(
                status=referral_status.upper()
            )

        return queryset

    def create(self, request, *args, **kwargs):
        user = request.user

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        pregnancy = serializer.validated_data["pregnancy"]
        to_facility = serializer.validated_data[
            "to_facility"
        ]

        if pregnancy.facility_id != user.facility_id:
            raise PermissionDenied(
                "The pregnancy does not belong to your facility."
            )

        try:
            referral = create_pnc_referral(
                pregnancy=pregnancy,
                referred_by=user,
                to_facility=to_facility,
                reason=serializer.validated_data["reason"],
                newborn=serializer.validated_data.get(
                    "newborn"
                ),
                **{
                    key: value
                    for key, value in serializer.validated_data.items()
                    if key not in [
                        "pregnancy",
                        "to_facility",
                        "reason",
                        "newborn",
                    ]
                },
            )
        except DjangoValidationError as exc:
            raise PermissionDenied(str(exc))

        return Response(
            self.get_serializer(referral).data,
            status=status.HTTP_201_CREATED,
        )


class PNCFollowUpViewSet(
    PNCScopedMixin,
    viewsets.ModelViewSet,
):
    queryset = PNCFollowUp.objects.select_related(
        "pregnancy",
        "newborn",
        "facility",
        "created_by",
        "completed_by",
    ).all()

    serializer_class = PNCFollowUpSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = [
        "get",
        "post",
        "patch",
        "head",
        "options",
    ]

    def get_queryset(self):
        return self.scoped_queryset(
            self.queryset
        )

    def create(self, request, *args, **kwargs):
        user = request.user

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        pregnancy = serializer.validated_data["pregnancy"]

        if pregnancy.facility_id != user.facility_id:
            raise PermissionDenied(
                "The pregnancy does not belong to your facility."
            )

        followup = create_pnc_followup(
            pregnancy=pregnancy,
            created_by=user,
            newborn=serializer.validated_data.get(
                "newborn"
            ),
            **{
                key: value
                for key, value in serializer.validated_data.items()
                if key not in [
                    "pregnancy",
                    "newborn",
                ]
            },
        )

        return Response(
            self.get_serializer(followup).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="complete",
    )
    def complete(self, request, pk=None):
        followup = self.get_object()

        try:
            followup = complete_pnc_followup(
                followup=followup,
                completed_by=request.user,
                notes=request.data.get(
                    "notes",
                    "",
                ),
            )
        except DjangoValidationError as exc:
            raise PermissionDenied(str(exc))

        return Response(
            self.get_serializer(followup).data,
            status=status.HTTP_200_OK,
        )