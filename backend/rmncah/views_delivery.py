from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models_delivery import (
    DeliveryRecord,
    NewbornRecord,
    LabourRecord,
    PostnatalMotherRecord,
)

from .serializers_delivery import (
    DeliveryRecordSerializer,
    NewbornRecordSerializer,
    LabourRecordSerializer,
    PostnatalMotherRecordSerializer,
)

from .services_delivery import (
    create_labour_record,
    record_delivery,
    record_newborn,
    create_postnatal_assessment,
)


class DeliveryScopedMixin:

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


class LabourRecordViewSet(
    DeliveryScopedMixin,
    viewsets.ModelViewSet,
):
    queryset = LabourRecord.objects.select_related(
        "pregnancy",
        "facility",
        "managed_by",
    ).all()

    serializer_class = LabourRecordSerializer
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

        pregnancy = serializer.validated_data[
            "pregnancy"
        ]

        if pregnancy.facility_id != user.facility_id:
            raise PermissionDenied(
                "The pregnancy does not belong to your facility."
            )

        try:
            labour = create_labour_record(
                pregnancy=pregnancy,
                managed_by=user,
                **{
                    key: value
                    for key, value in serializer.validated_data.items()
                    if key != "pregnancy"
                },
            )
        except DjangoValidationError as exc:
            raise PermissionDenied(str(exc))

        return Response(
            self.get_serializer(labour).data,
            status=status.HTTP_201_CREATED,
        )


class DeliveryRecordViewSet(
    DeliveryScopedMixin,
    viewsets.ModelViewSet,
):
    queryset = DeliveryRecord.objects.select_related(
        "pregnancy",
        "facility",
        "attended_by",
    ).all()

    serializer_class = DeliveryRecordSerializer
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

        delivery_mode = self.request.query_params.get(
            "delivery_mode"
        )

        if delivery_mode:
            queryset = queryset.filter(
                delivery_mode=delivery_mode
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

        try:
            delivery = record_delivery(
                pregnancy=pregnancy,
                attended_by=user,
                **{
                    key: value
                    for key, value in serializer.validated_data.items()
                    if key != "pregnancy"
                },
            )
        except DjangoValidationError as exc:
            raise PermissionDenied(str(exc))

        return Response(
            self.get_serializer(delivery).data,
            status=status.HTTP_201_CREATED,
        )


class NewbornRecordViewSet(
    DeliveryScopedMixin,
    viewsets.ModelViewSet,
):
    queryset = NewbornRecord.objects.select_related(
        "delivery",
        "pregnancy",
        "facility",
        "recorded_by",
    ).all()

    serializer_class = NewbornRecordSerializer
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

        delivery = self.request.query_params.get(
            "delivery"
        )

        if delivery:
            queryset = queryset.filter(
                delivery_id=delivery
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

        delivery = serializer.validated_data[
            "delivery"
        ]

        if delivery.facility_id != user.facility_id:
            raise PermissionDenied(
                "The delivery does not belong to your facility."
            )

        if serializer.validated_data[
            "pregnancy"
        ].id != delivery.pregnancy_id:
            raise PermissionDenied(
                "The pregnancy does not match the delivery."
            )

        newborn = record_newborn(
            delivery=delivery,
            recorded_by=user,
            **{
                key: value
                for key, value in serializer.validated_data.items()
                if key != "delivery"
                and key != "pregnancy"
            },
        )

        return Response(
            self.get_serializer(newborn).data,
            status=status.HTTP_201_CREATED,
        )


class PostnatalMotherRecordViewSet(
    DeliveryScopedMixin,
    viewsets.ModelViewSet,
):
    queryset = PostnatalMotherRecord.objects.select_related(
        "pregnancy",
        "delivery",
        "facility",
        "reviewed_by",
    ).all()

    serializer_class = PostnatalMotherRecordSerializer
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

        delivery = self.request.query_params.get(
            "delivery"
        )

        if delivery:
            queryset = queryset.filter(
                delivery_id=delivery
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

        delivery = serializer.validated_data[
            "delivery"
        ]

        if delivery.facility_id != user.facility_id:
            raise PermissionDenied(
                "The delivery does not belong to your facility."
            )

        record = create_postnatal_assessment(
            delivery=delivery,
            reviewed_by=user,
            **{
                key: value
                for key, value in serializer.validated_data.items()
                if key != "delivery"
                and key != "pregnancy"
            },
        )

        return Response(
            self.get_serializer(record).data,
            status=status.HTTP_201_CREATED,
        )