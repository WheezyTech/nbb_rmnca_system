from django.contrib import admin
from .models import Region, County, Facility


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    search_fields = ("name", "code")


@admin.register(County)
class CountyAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "region", "is_active")
    search_fields = ("name", "code", "region__name")
    list_filter = ("region", "is_active")


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "facility_code",
        "facility_type",
        "county",
        "region",
        "is_blood_bank",
        "has_rmnca_services",
        "is_active",
    )

    search_fields = (
        "name",
        "facility_code",
        "county__name",
        "region__name",
    )

    list_filter = (
        "facility_type",
        "region",
        "county",
        "is_blood_bank",
        "has_rmnca_services",
        "is_active",
    )