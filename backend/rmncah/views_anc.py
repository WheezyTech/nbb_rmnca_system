from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models_anc import (
    ANCClient,
    PregnancyRecord,
    ANCVisit,
    ANCRiskAssessment,
    ANCInvestigation,
    ANCReferral,
    ANCClinicalEvent,
)

from .serializers_anc import (
    ANCClientSerializer,
    PregnancyRecordSerializer,
    ANCVisitSerializer,
    ANCRiskAssessmentSerializer,
    ANCInvestigationSerializer,
    ANCReferralSerializer,
    ANCClinicalEventSerializer,
)

from .services_anc import (
    register_anc_client,
    create_pregnancy,
    complete_anc_visit,
    assess_anc_risk,
    create_anc_investigation,
    create_anc_referral,
)


class ANCScopedMixin:

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


class ANCClientViewSet(
    ANCScopedMixin,
    viewsets.ModelViewSet,
):
    queryset = ANCClient.objects.select_related(
        "facility",
        "registered_by",
    ).all()

    serializer_class = ANCClientSerializer
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

        patient_reference = self.request.query_params.get(
            "patient_reference"
        )

        if patient_reference:
            queryset = queryset.filter(
                patient_reference__icontains=patient_reference
            )

        status_filter = self.request.query_params.get(
            "status"
        )

        if status_filter:
            queryset = queryset.filter(
                status=status_filter.upper()
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

        try:
            client = register_anc_client(
                facility=user.facility,
                registered_by=user,
                **serializer.validated_data,
            )
        except DjangoValidationError as exc:
            raise PermissionDenied(str(exc))

        output = self.get_serializer(client)

        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )


class PregnancyRecordViewSet(
    ANCScopedMixin,
    viewsets.ModelViewSet,
):
    queryset = PregnancyRecord.objects.select_related(
        "client",
        "facility",
        "created_by",
    ).all()

    serializer_class = PregnancyRecordSerializer
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

        status_filter = self.request.query_params.get(
            "status"
        )

        if status_filter:
            queryset = queryset.filter(
                status=status_filter.upper()
            )

        high_risk = self.request.query_params.get(
            "high_risk"
        )

        if high_risk is not None:
            queryset = queryset.filter(
                high_risk=high_risk.lower() == "true"
            )

        client = self.request.query_params.get(
            "client"
        )

        if client:
            queryset = queryset.filter(
                client_id=client
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

        client = serializer.validated_data["client"]

        if client.facility_id != user.facility_id:
            raise PermissionDenied(
                "The client does not belong to your facility."
            )

        try:
            pregnancy = create_pregnancy(
                client=client,
                created_by=user,
                **{
                    key: value
                    for key, value in serializer.validated_data.items()
                    if key != "client"
                },
            )
        except DjangoValidationError as exc:
            raise PermissionDenied(str(exc))

        output = self.get_serializer(pregnancy)

        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="timeline",
    )
    def timeline(self, request, pk=None):
        pregnancy = self.get_object()

        events = pregnancy.clinical_events.select_related(
            "performed_by",
            "facility",
        ).order_by("created_at")

        serializer = ANCClinicalEventSerializer(
            events,
            many=True,
        )

        return Response(serializer.data)


class ANCVisitViewSet(
    ANCScopedMixin,
    viewsets.ModelViewSet,
):
    queryset = ANCVisit.objects.select_related(
        "pregnancy",
        "facility",
        "attended_by",
    ).all()

    serializer_class = ANCVisitSerializer
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

        visit_type = self.request.query_params.get(
            "visit_type"
        )

        if visit_type:
            queryset = queryset.filter(
                visit_type=visit_type.upper()
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

        pregnancy = serializer.validated_data[
            "pregnancy"
        ]

        if pregnancy.facility_id != user.facility_id:
            raise PermissionDenied(
                "The pregnancy does not belong to your facility."
            )

        visit = complete_anc_visit(
            pregnancy=pregnancy,
            attended_by=user,
            **{
                key: value
                for key, value in serializer.validated_data.items()
                if key != "pregnancy"
            },
        )

        output = self.get_serializer(visit)

        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )


class ANCRiskAssessmentViewSet(
    ANCScopedMixin,
    viewsets.ModelViewSet,
):
    queryset = ANCRiskAssessment.objects.select_related(
        "pregnancy",
        "anc_visit",
        "facility",
        "assessed_by",
    ).all()

    serializer_class = ANCRiskAssessmentSerializer
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

        risk_level = self.request.query_params.get(
            "risk_level"
        )

        if risk_level:
            queryset = queryset.filter(
                risk_level=risk_level.upper()
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

        pregnancy = serializer.validated_data[
            "pregnancy"
        ]

        if pregnancy.facility_id != user.facility_id:
            raise PermissionDenied(
                "The pregnancy does not belong to your facility."
            )

        assessment = assess_anc_risk(
            pregnancy=pregnancy,
            assessed_by=user,
            **{
                key: value
                for key, value in serializer.validated_data.items()
                if key != "pregnancy"
            },
        )

        output = self.get_serializer(assessment)

        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )


class ANCInvestigationViewSet(
    ANCScopedMixin,
    viewsets.ModelViewSet,
):
    queryset = ANCInvestigation.objects.select_related(
        "pregnancy",
        "anc_visit",
        "facility",
        "ordered_by",
    ).all()

    serializer_class = ANCInvestigationSerializer
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

        investigation_status = self.request.query_params.get(
            "status"
        )

        if investigation_status:
            queryset = queryset.filter(
                status=investigation_status.upper()
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

        pregnancy = serializer.validated_data[
            "pregnancy"
        ]

        if pregnancy.facility_id != user.facility_id:
            raise PermissionDenied(
                "The pregnancy does not belong to your facility."
            )

        investigation = create_anc_investigation(
            pregnancy=pregnancy,
            ordered_by=user,
            **{
                key: value
                for key, value in serializer.validated_data.items()
                if key != "pregnancy"
            },
        )

        output = self.get_serializer(
            investigation
        )

        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )


class ANCReferralViewSet(
    ANCScopedMixin,
    viewsets.ModelViewSet,
):
    queryset = ANCReferral.objects.select_related(
        "pregnancy",
        "anc_visit",
        "from_facility",
        "to_facility",
        "referred_by",
    ).all()

    serializer_class = ANCReferralSerializer
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

        urgency = self.request.query_params.get(
            "urgency"
        )

        if urgency:
            queryset = queryset.filter(
                urgency=urgency.upper()
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

        pregnancy = serializer.validated_data[
            "pregnancy"
        ]

        if pregnancy.facility_id != user.facility_id:
            raise PermissionDenied(
                "The pregnancy does not belong to your facility."
            )

        referral = create_anc_referral(
            pregnancy=pregnancy,
            referred_by=user,
            to_facility=serializer.validated_data[
                "to_facility"
            ],
            reason=serializer.validated_data[
                "reason"
            ],
            **{
                key: value
                for key, value in serializer.validated_data.items()
                if key not in {
                    "pregnancy",
                    "to_facility",
                    "reason",
                }
            },
        )

        output = self.get_serializer(referral)

        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )


class ANCClinicalEventViewSet(
    ANCScopedMixin,
    viewsets.ReadOnlyModelViewSet,
):
    queryset = ANCClinicalEvent.objects.select_related(
        "pregnancy",
        "facility",
        "performed_by",
    ).all()

    serializer_class = ANCClinicalEventSerializer
    permission_classes = [IsAuthenticated]

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

        event_type = self.request.query_params.get(
            "event_type"
        )

        if event_type:
            queryset = queryset.filter(
                event_type=event_type.upper()
            )

        return queryset