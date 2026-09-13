from rest_framework import serializers
from .models import Region, County, Facility


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = [
            "id",
            "name",
            "code",
            "is_active",
        ]


class CountySerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(
        source="region.name",
        read_only=True,
    )

    class Meta:
        model = County
        fields = [
            "id",
            "name",
            "code",
            "region",
            "region_name",
            "is_active",
        ]


class FacilitySerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(
        source="region.name",
        read_only=True,
    )

    county_name = serializers.CharField(
        source="county.name",
        read_only=True,
    )

    class Meta:
        model = Facility
        fields = [
            "id",
            "name",
            "facility_code",
            "facility_type",
            "region",
            "region_name",
            "county",
            "county_name",
            "address",
            "phone",
            "email",
            "is_blood_bank",
            "has_rmnca_services",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        region = attrs.get(
            "region",
            getattr(self.instance, "region", None)
        )

        county = attrs.get(
            "county",
            getattr(self.instance, "county", None)
        )

        if region and county and county.region_id != region.id:
            raise serializers.ValidationError({
                "county": "The selected county does not belong to the selected region."
            })

        return attrs