import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class RMNCAHServiceCategory(models.Model):
    """
    High-level grouping of RMNCAH services.
    """

    class CategoryCode(models.TextChoices):
        MATERNAL = "MATERNAL", "Maternal Health"
        NEWBORN = "NEWBORN", "Newborn Health"
        CHILD = "CHILD", "Child Health"
        ADOLESCENT = "ADOLESCENT", "Adolescent Health"
        FAMILY_PLANNING = "FAMILY_PLANNING", "Family Planning"
        REPRODUCTIVE = "REPRODUCTIVE", "Reproductive Health"
        ANC = "ANC", "Antenatal Care"
        PNC = "PNC", "Postnatal Care"
        MATERNITY = "MATERNITY", "Maternity Services"
        IMMUNIZATION = "IMMUNIZATION", "Immunization"
        OTHER = "OTHER", "Other RMNCAH Service"

    category_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    code = models.CharField(
        max_length=40,
        unique=True,
    )

    name = models.CharField(
        max_length=150,
    )

    category_type = models.CharField(
        max_length=30,
        choices=CategoryCode.choices,
        default=CategoryCode.OTHER,
    )

    description = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    display_order = models.PositiveIntegerField(
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "RMNCAH Service Category"
        verbose_name_plural = "RMNCAH Service Categories"

    def save(self, *args, **kwargs):
        if not self.category_id:
            self.category_id = (
                f"RMNCAH-CAT-{uuid.uuid4().hex[:12].upper()}"
            )

        self.code = self.code.strip().upper()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"


class RMNCAHService(models.Model):
    """
    Individual RMNCAH service offered within a facility.
    """

    service_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    category = models.ForeignKey(
        RMNCAHServiceCategory,
        on_delete=models.PROTECT,
        related_name="services",
    )

    code = models.CharField(
        max_length=50,
        unique=True,
    )

    name = models.CharField(
        max_length=200,
    )

    description = models.TextField(
        blank=True,
    )

    requires_clinical_staff = models.BooleanField(
        default=True,
    )

    requires_referral = models.BooleanField(
        default=False,
    )

    is_emergency_service = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    display_order = models.PositiveIntegerField(
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["category", "display_order", "name"]
        verbose_name = "RMNCAH Service"
        verbose_name_plural = "RMNCAH Services"

    def save(self, *args, **kwargs):
        if not self.service_id:
            self.service_id = (
                f"RMNCAH-SVC-{uuid.uuid4().hex[:12].upper()}"
            )

        self.code = self.code.strip().upper()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"


class RMNCAHDepartment(models.Model):
    """
    RMNCAH-related department, unit or clinical area
    within a facility.
    """

    department_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="rmncah_departments",
    )

    code = models.CharField(
        max_length=50,
    )

    name = models.CharField(
        max_length=200,
    )

    description = models.TextField(
        blank=True,
    )

    head_name = models.CharField(
        max_length=150,
        blank=True,
    )

    contact_phone = models.CharField(
        max_length=30,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["facility", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["facility", "code"],
                name="unique_rmncah_department_code_per_facility",
            ),
        ]
        verbose_name = "RMNCAH Department"
        verbose_name_plural = "RMNCAH Departments"

    def save(self, *args, **kwargs):
        if not self.department_id:
            self.department_id = (
                f"RMNCAH-DEPT-{uuid.uuid4().hex[:12].upper()}"
            )

        self.code = self.code.strip().upper()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.facility.name} - {self.name}"


class RMNCAHServicePoint(models.Model):
    """
    Specific location where an RMNCAH service is delivered.
    """

    class ServicePointType(models.TextChoices):
        CLINIC = "CLINIC", "Clinic"
        WARD = "WARD", "Ward"
        MATERNITY = "MATERNITY", "Maternity"
        LABOUR_WARD = "LABOUR_WARD", "Labour Ward"
        THEATRE = "THEATRE", "Theatre"
        ANC = "ANC", "ANC Clinic"
        PNC = "PNC", "PNC Clinic"
        CHILD_WELFARE = "CHILD_WELFARE", "Child Welfare Clinic"
        FAMILY_PLANNING = "FAMILY_PLANNING", "Family Planning Clinic"
        IMMUNIZATION = "IMMUNIZATION", "Immunization Clinic"
        NEWBORN = "NEWBORN", "Newborn Unit"
        OTHER = "OTHER", "Other"

    service_point_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="rmncah_service_points",
    )

    department = models.ForeignKey(
        RMNCAHDepartment,
        on_delete=models.PROTECT,
        related_name="service_points",
        null=True,
        blank=True,
    )

    code = models.CharField(
        max_length=50,
    )

    name = models.CharField(
        max_length=200,
    )

    point_type = models.CharField(
        max_length=30,
        choices=ServicePointType.choices,
        default=ServicePointType.OTHER,
    )

    location_description = models.CharField(
        max_length=255,
        blank=True,
    )

    contact_phone = models.CharField(
        max_length=30,
        blank=True,
    )

    is_24_hour = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["facility", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["facility", "code"],
                name="unique_rmncah_service_point_code_per_facility",
            ),
        ]
        verbose_name = "RMNCAH Service Point"
        verbose_name_plural = "RMNCAH Service Points"

    def save(self, *args, **kwargs):
        if not self.service_point_id:
            self.service_point_id = (
                f"RMNCAH-POINT-{uuid.uuid4().hex[:12].upper()}"
            )

        self.code = self.code.strip().upper()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.facility.name} - {self.name}"


class RMNCAHFacilityProfile(models.Model):
    """
    Overall RMNCAH capability/configuration for a facility.
    """

    profile_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    facility = models.OneToOneField(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="rmncah_profile",
    )

    rmncah_enabled = models.BooleanField(
        default=True,
    )

    maternal_services_available = models.BooleanField(
        default=False,
    )

    newborn_services_available = models.BooleanField(
        default=False,
    )

    child_health_services_available = models.BooleanField(
        default=False,
    )

    adolescent_services_available = models.BooleanField(
        default=False,
    )

    family_planning_available = models.BooleanField(
        default=False,
    )

    reproductive_health_available = models.BooleanField(
        default=False,
    )

    emergency_obstetric_care = models.BooleanField(
        default=False,
    )

    newborn_emergency_care = models.BooleanField(
        default=False,
    )

    caesarean_section_available = models.BooleanField(
        default=False,
    )

    blood_transfusion_available = models.BooleanField(
        default=False,
    )

    referral_services_available = models.BooleanField(
        default=True,
    )

    ambulance_available = models.BooleanField(
        default=False,
    )

    operating_hours = models.CharField(
        max_length=255,
        blank=True,
    )

    service_capacity_notes = models.TextField(
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "RMNCAH Facility Profile"
        verbose_name_plural = "RMNCAH Facility Profiles"

    def save(self, *args, **kwargs):
        if not self.profile_id:
            self.profile_id = (
                f"RMNCAH-PROFILE-{uuid.uuid4().hex[:12].upper()}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"RMNCAH Profile - {self.facility.name}"


class RMNCAHFacilityService(models.Model):
    """
    Connects an RMNCAH service to a specific facility and
    stores facility-specific availability/capability.
    """

    class Availability(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        LIMITED = "LIMITED", "Limited"
        TEMPORARILY_UNAVAILABLE = (
            "TEMPORARILY_UNAVAILABLE",
            "Temporarily Unavailable",
        )
        NOT_AVAILABLE = "NOT_AVAILABLE", "Not Available"

    facility_service_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="rmncah_services",
    )

    service = models.ForeignKey(
        RMNCAHService,
        on_delete=models.PROTECT,
        related_name="facility_services",
    )

    service_point = models.ForeignKey(
        RMNCAHServicePoint,
        on_delete=models.PROTECT,
        related_name="facility_services",
        null=True,
        blank=True,
    )

    availability = models.CharField(
        max_length=40,
        choices=Availability.choices,
        default=Availability.AVAILABLE,
    )

    is_24_hour = models.BooleanField(
        default=False,
    )

    emergency_available = models.BooleanField(
        default=False,
    )

    referral_required = models.BooleanField(
        default=False,
    )

    minimum_staff_required = models.PositiveIntegerField(
        default=0,
    )

    current_staff_count = models.PositiveIntegerField(
        default=0,
    )

    estimated_daily_capacity = models.PositiveIntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
        ],
    )

    operating_hours = models.CharField(
        max_length=255,
        blank=True,
    )

    last_verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    configured_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rmncah_facility_services_configured",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["facility", "service__category", "service__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["facility", "service"],
                name="unique_rmncah_service_per_facility",
            ),
        ]
        verbose_name = "Facility RMNCAH Service"
        verbose_name_plural = "Facility RMNCAH Services"

    def save(self, *args, **kwargs):
        if not self.facility_service_id:
            self.facility_service_id = (
                f"RMNCAH-FS-{uuid.uuid4().hex[:12].upper()}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.facility.name} - {self.service.name}"
    
from .models_anc import (
    ANCClient,
    PregnancyRecord,
    ANCVisit,
    ANCRiskAssessment,
    ANCInvestigation,
    ANCReferral,
    ANCClinicalEvent,
)

from .models_delivery import (
    DeliveryRecord,
    NewbornRecord,
    LabourRecord,
    PostnatalMotherRecord,
)

from .models_pnc import (
    PNCVisit,
    NewbornCareRecord,
    PNCReferral,
    PNCFollowUp,
)