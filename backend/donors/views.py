from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from accounts.access import (
    filter_by_facility_scope,
    get_user_scope,
)

from .models import (
    Donor,
    Donation,
    DonorEligibility,
    DeferralRecord,
    BloodSample,
    LaboratoryTest,
    BloodUnit,
)

from .serializers import (
    DonorSerializer,
    DonationSerializer,
    DonorEligibilitySerializer,
    DeferralRecordSerializer,
    BloodSampleSerializer,
    LaboratoryTestSerializer,
    BloodUnitSerializer,
)


class DonorViewSet(viewsets.ModelViewSet):

    queryset = Donor.objects.all()
    serializer_class = DonorSerializer
    permission_classes = [IsAuthenticated]

    search_fields = [
        "donor_id",
        "national_id",
        "first_name",
        "middle_name",
        "last_name",
        "phone",
        "email",
    ]

    ordering_fields = [
        "registered_at",
        "first_name",
        "last_name",
        "blood_group",
    ]

    def get_queryset(self):

        queryset = super().get_queryset()
        user = self.request.user

        if user.role in [
            "SUPER_ADMIN",
            "NATIONAL_ADMIN",
        ]:
            pass

        elif user.role == "REGIONAL_ADMIN":

            if not user.facility_id:
                return queryset.none()

            queryset = queryset.filter(
                donations__facility__region_id=(
                    user.facility.region_id
                )
            )

        elif user.role == "COUNTY_ADMIN":

            if not user.facility_id:
                return queryset.none()

            queryset = queryset.filter(
                donations__facility__county_id=(
                    user.facility.county_id
                )
            )

        else:

            if not user.facility_id:
                return queryset.none()

            queryset = queryset.filter(
                donations__facility_id=user.facility_id
            )

        queryset = queryset.distinct()

        status = self.request.query_params.get(
            "status"
        )

        blood_group = self.request.query_params.get(
            "blood_group"
        )

        if status:
            queryset = queryset.filter(
                status=status
            )

        if blood_group:
            queryset = queryset.filter(
                blood_group=blood_group
            )

        return queryset

class DonationViewSet(viewsets.ModelViewSet):

    queryset = Donation.objects.select_related(
        "donor",
        "facility",
    ).all()

    serializer_class = DonationSerializer
    permission_classes = [IsAuthenticated]

    search_fields = [
        "donation_id",
        "donor__donor_id",
        "donor__first_name",
        "donor__last_name",
        "facility__name",
    ]

    ordering_fields = [
        "collection_date",
        "created_at",
        "status",
    ]

    def get_queryset(self):

        queryset = super().get_queryset()
        user = self.request.user

        return filter_by_facility_scope(
            queryset,
            user,
            facility_field="facility_id",
        )

    def perform_create(self, serializer):

        user = self.request.user

        if user.role in [
            "SUPER_ADMIN",
            "NATIONAL_ADMIN",
        ]:
            serializer.save()
            return

        if not user.facility_id:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "Your account is not assigned to a facility."
            )

        serializer.save(
            facility=user.facility
        )

class DonorEligibilityViewSet(
    viewsets.ModelViewSet
):

    queryset = DonorEligibility.objects.select_related(
        "donor",
        "assessed_by",
    ).all()

    serializer_class = DonorEligibilitySerializer
    permission_classes = [IsAuthenticated]

    search_fields = [
        "donor__donor_id",
        "donor__first_name",
        "donor__last_name",
    ]

    def get_queryset(self):

        queryset = super().get_queryset()
        user = self.request.user

        scope = get_user_scope(user)

        if scope == "national":
            return queryset

        if not user.facility_id:
            return queryset.none()

        return queryset.filter(
            donor__donations__facility_id=user.facility_id
        ).distinct()


class DeferralRecordViewSet(
    viewsets.ModelViewSet
):

    queryset = DeferralRecord.objects.select_related(
        "donor",
        "recorded_by",
    ).all()

    serializer_class = DeferralRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        queryset = super().get_queryset()
        user = self.request.user

        scope = get_user_scope(user)

        if scope == "national":
            return queryset

        if not user.facility_id:
            return queryset.none()

        return queryset.filter(
            donor__donations__facility_id=user.facility_id
        ).distinct()


class BloodSampleViewSet(viewsets.ModelViewSet):

    queryset = BloodSample.objects.select_related(
        "donation",
        "donation__donor",
    ).all()

    serializer_class = BloodSampleSerializer
    permission_classes = [IsAuthenticated]

    search_fields = [
        "sample_id",
        "donation__donation_id",
        "donation__donor__donor_id",
    ]

    def get_queryset(self):

        queryset = super().get_queryset()
        user = self.request.user

        scope = get_user_scope(user)

        if scope == "national":
            return queryset

        if not user.facility_id:
            return queryset.none()

        return queryset.filter(
            donation__facility_id=user.facility_id
        )


class LaboratoryTestViewSet(
    viewsets.ModelViewSet
):

    queryset = LaboratoryTest.objects.select_related(
        "sample",
        "performed_by",
    ).all()

    serializer_class = LaboratoryTestSerializer
    permission_classes = [IsAuthenticated]

    search_fields = [
        "test_id",
        "sample__sample_id",
        "sample__donation__donation_id",
    ]

    def get_queryset(self):

        queryset = super().get_queryset()
        user = self.request.user

        scope = get_user_scope(user)

        if scope == "national":
            return queryset

        if not user.facility_id:
            return queryset.none()

        return queryset.filter(
            sample__donation__facility_id=user.facility_id
        )


class BloodUnitViewSet(viewsets.ModelViewSet):

    queryset = BloodUnit.objects.select_related(
        "donation",
        "facility",
    ).all()

    serializer_class = BloodUnitSerializer
    permission_classes = [IsAuthenticated]

    search_fields = [
        "unit_id",
        "barcode",
        "blood_group",
        "component_type",
    ]

    def get_queryset(self):

        queryset = super().get_queryset()
        user = self.request.user

        return filter_by_facility_scope(
            queryset,
            user,
            facility_field="facility_id",
        )

    def perform_create(self, serializer):

        user = self.request.user

        if user.role in [
            "SUPER_ADMIN",
            "NATIONAL_ADMIN",
        ]:
            serializer.save()
            return

        if not user.facility_id:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "Your account is not assigned to a facility."
            )

        serializer.save(
            facility=user.facility
        )