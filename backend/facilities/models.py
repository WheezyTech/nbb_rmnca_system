from django.db import models


class Region(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class County(models.Model):
    region = models.ForeignKey(
        Region,
        on_delete=models.PROTECT,
        related_name="counties",
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Facility(models.Model):

    class FacilityType(models.TextChoices):
        NATIONAL_BLOOD_CENTRE = (
            "NATIONAL_BLOOD_CENTRE",
            "National Blood Centre",
        )
        REGIONAL_BLOOD_CENTRE = (
            "REGIONAL_BLOOD_CENTRE",
            "Regional Blood Centre",
        )
        COUNTY_HOSPITAL = (
            "COUNTY_HOSPITAL",
            "County Hospital",
        )
        SUB_COUNTY_HOSPITAL = (
            "SUB_COUNTY_HOSPITAL",
            "Sub-County Hospital",
        )
        HEALTH_CENTRE = (
            "HEALTH_CENTRE",
            "Health Centre",
        )
        DISPENSARY = (
            "DISPENSARY",
            "Dispensary",
        )
        PRIVATE_HOSPITAL = (
            "PRIVATE_HOSPITAL",
            "Private Hospital",
        )
        OTHER = "OTHER", "Other"

    region = models.ForeignKey(
        Region,
        on_delete=models.PROTECT,
        related_name="facilities",
    )

    county = models.ForeignKey(
        County,
        on_delete=models.PROTECT,
        related_name="facilities",
    )

    name = models.CharField(max_length=200)

    facility_code = models.CharField(
        max_length=50,
        unique=True,
    )

    facility_type = models.CharField(
        max_length=50,
        choices=FacilityType.choices,
    )

    address = models.TextField(blank=True)

    phone = models.CharField(
        max_length=20,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    is_blood_bank = models.BooleanField(
        default=False
    )

    has_rmnca_services = models.BooleanField(
        default=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.facility_code})"