from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import (
    IsNationalAdmin,
)

from .models import Region, County, Facility
from .serializers import (
    RegionSerializer,
    CountySerializer,
    FacilitySerializer,
)


class RegionViewSet(viewsets.ModelViewSet):

    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [IsAuthenticated]

    search_fields = ["name", "code"]
    ordering_fields = ["name", "code"]


class CountyViewSet(viewsets.ModelViewSet):

    queryset = County.objects.select_related("region").all()
    serializer_class = CountySerializer
    permission_classes = [IsAuthenticated]

    search_fields = [
        "name",
        "code",
        "region__name",
    ]

    ordering_fields = [
        "name",
        "code",
    ]

    def get_queryset(self):

        queryset = super().get_queryset()

        region_id = self.request.query_params.get("region")

        if region_id:
            queryset = queryset.filter(
                region_id=region_id
            )

        return queryset


class FacilityViewSet(viewsets.ModelViewSet):

    queryset = Facility.objects.select_related(
        "region",
        "county",
    ).all()

    serializer_class = FacilitySerializer

    search_fields = [
        "name",
        "facility_code",
        "address",
        "phone",
        "email",
        "county__name",
        "region__name",
    ]

    ordering_fields = [
        "name",
        "facility_code",
        "facility_type",
        "created_at",
    ]

    def get_permissions(self):

        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
        ]:
            return [IsNationalAdmin()]

        return [IsAuthenticated()]

    def get_queryset(self):

        queryset = super().get_queryset()
        user = self.request.user

        if user.role in [
            "SUPER_ADMIN",
            "NATIONAL_ADMIN",
        ]:
            pass

        elif user.role == "REGIONAL_ADMIN":

            if user.facility_id:
                queryset = queryset.filter(
                    region_id=user.facility.region_id
                )
            else:
                queryset = queryset.none()

        elif user.role == "COUNTY_ADMIN":

            if user.facility_id:
                queryset = queryset.filter(
                    county_id=user.facility.county_id
                )
            else:
                queryset = queryset.none()

        else:

            if user.facility_id:
                queryset = queryset.filter(
                    id=user.facility_id
                )
            else:
                queryset = queryset.none()

        region_id = self.request.query_params.get("region")
        county_id = self.request.query_params.get("county")
        facility_type = self.request.query_params.get(
            "facility_type"
        )

        if region_id:
            queryset = queryset.filter(
                region_id=region_id
            )

        if county_id:
            queryset = queryset.filter(
                county_id=county_id
            )

        if facility_type:
            queryset = queryset.filter(
                facility_type=facility_type
            )

        return queryset