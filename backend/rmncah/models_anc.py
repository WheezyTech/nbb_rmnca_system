import uuid

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class ANCClient(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        TRANSFERRED = "TRANSFERRED", "Transferred"
        COMPLETED = "COMPLETED", "Completed"
        LOST_TO_FOLLOWUP = "LOST_TO_FOLLOWUP", "Lost to Follow-up"

    client_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="anc_clients",
    )

    patient_reference = models.CharField(
        max_length=100,
    )

    national_patient_number = models.CharField(
        max_length=100,
        blank=True,
    )

    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)

    date_of_birth = models.DateField(
        null=True,
        blank=True,
    )

    phone_number = models.CharField(
        max_length=30,
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    gravida = models.PositiveIntegerField(
        default=1,
    )

    para = models.PositiveIntegerField(
        default=0,
    )

    living_children = models.PositiveIntegerField(
        default=0,
    )

    abortions = models.PositiveIntegerField(
        default=0,
    )

    stillbirths = models.PositiveIntegerField(
        default=0,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="anc_clients_registered",
    )

    registered_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-registered_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["facility", "patient_reference"],
                name="unique_anc_patient_reference_per_facility",
            )
        ]

    def save(self, *args, **kwargs):
        if not self.client_id:
            self.client_id = (
                f"ANC-CLIENT-{uuid.uuid4().hex[:12].upper()}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.client_id


class PregnancyRecord(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        DELIVERED = "DELIVERED", "Delivered"
        ABORTED = "ABORTED", "Aborted"
        MISCARRIAGE = "MISCARRIAGE", "Miscarriage"
        STILLBIRTH = "STILLBIRTH", "Stillbirth"
        TRANSFERRED = "TRANSFERRED", "Transferred"
        CLOSED = "CLOSED", "Closed"

    class PregnancyType(models.TextChoices):
        SINGLETON = "SINGLETON", "Singleton"
        MULTIPLE = "MULTIPLE", "Multiple"
        UNKNOWN = "UNKNOWN", "Unknown"

    pregnancy_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    client = models.ForeignKey(
        ANCClient,
        on_delete=models.PROTECT,
        related_name="pregnancies",
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="pregnancies",
    )

    last_menstrual_period = models.DateField(
        null=True,
        blank=True,
    )

    expected_delivery_date = models.DateField(
        null=True,
        blank=True,
    )

    pregnancy_type = models.CharField(
        max_length=20,
        choices=PregnancyType.choices,
        default=PregnancyType.UNKNOWN,
    )

    estimated_gestational_age_weeks = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MaxValueValidator(45)],
    )

    gravida = models.PositiveIntegerField(
        default=1,
    )

    para = models.PositiveIntegerField(
        default=0,
    )

    high_risk = models.BooleanField(
        default=False,
    )

    risk_summary = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    pregnancy_outcome = models.TextField(
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pregnancies_created",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.pregnancy_id:
            self.pregnancy_id = (
                f"PREG-{uuid.uuid4().hex[:12].upper()}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.pregnancy_id


class ANCVisit(models.Model):
    class VisitType(models.TextChoices):
        BOOKING = "BOOKING", "ANC Booking"
        ROUTINE = "ROUTINE", "Routine ANC Visit"
        FOLLOW_UP = "FOLLOW_UP", "Follow-up"
        EMERGENCY = "EMERGENCY", "Emergency"
        HIGH_RISK = "HIGH_RISK", "High Risk Review"
        REFERRAL = "REFERRAL", "Referral Review"

    class Status(models.TextChoices):
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        MISSED = "MISSED", "Missed"

    visit_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    pregnancy = models.ForeignKey(
        PregnancyRecord,
        on_delete=models.PROTECT,
        related_name="anc_visits",
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="anc_visits",
    )

    visit_number = models.PositiveIntegerField(
        default=1,
    )

    visit_type = models.CharField(
        max_length=30,
        choices=VisitType.choices,
        default=VisitType.ROUTINE,
    )

    visit_date = models.DateTimeField()

    gestational_age_weeks = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MaxValueValidator(45)],
    )

    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )

    height_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )

    systolic_bp = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    diastolic_bp = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    pulse_rate = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    temperature_c = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
    )

    respiratory_rate = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    fundal_height_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    foetal_heart_rate = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    foetal_movement_present = models.BooleanField(
        null=True,
        blank=True,
    )

    oedema_present = models.BooleanField(
        null=True,
        blank=True,
    )

    symptoms = models.TextField(
        blank=True,
    )

    clinical_findings = models.TextField(
        blank=True,
    )

    assessment = models.TextField(
        blank=True,
    )

    plan = models.TextField(
        blank=True,
    )

    next_visit_date = models.DateField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.COMPLETED,
    )

    attended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="anc_visits_attended",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-visit_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["pregnancy", "visit_number"],
                name="unique_anc_visit_number_per_pregnancy",
            )
        ]

    def save(self, *args, **kwargs):
        if not self.visit_id:
            self.visit_id = (
                f"ANC-VISIT-{uuid.uuid4().hex[:12].upper()}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.visit_id


class ANCRiskAssessment(models.Model):
    class RiskLevel(models.TextChoices):
        LOW = "LOW", "Low Risk"
        MODERATE = "MODERATE", "Moderate Risk"
        HIGH = "HIGH", "High Risk"
        CRITICAL = "CRITICAL", "Critical Risk"

    assessment_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    pregnancy = models.ForeignKey(
        PregnancyRecord,
        on_delete=models.PROTECT,
        related_name="risk_assessments",
    )

    anc_visit = models.ForeignKey(
        ANCVisit,
        on_delete=models.PROTECT,
        related_name="risk_assessments",
        null=True,
        blank=True,
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="anc_risk_assessments",
    )

    risk_level = models.CharField(
        max_length=20,
        choices=RiskLevel.choices,
    )

    hypertension = models.BooleanField(default=False)
    diabetes = models.BooleanField(default=False)
    anaemia = models.BooleanField(default=False)
    previous_cesarean = models.BooleanField(default=False)
    previous_postpartum_haemorrhage = models.BooleanField(default=False)
    multiple_pregnancy = models.BooleanField(default=False)
    previous_stillbirth = models.BooleanField(default=False)
    previous_neonatal_death = models.BooleanField(default=False)
    bleeding = models.BooleanField(default=False)
    severe_headache = models.BooleanField(default=False)
    reduced_foetal_movement = models.BooleanField(default=False)
    other_risk_factor = models.BooleanField(default=False)

    risk_factors = models.TextField(
        blank=True,
    )

    clinical_action = models.TextField(
        blank=True,
    )

    referral_required = models.BooleanField(
        default=False,
    )

    assessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="anc_risk_assessments_created",
    )

    assessed_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-assessed_at"]

    def save(self, *args, **kwargs):
        if not self.assessment_id:
            self.assessment_id = (
                f"ANC-RISK-{uuid.uuid4().hex[:12].upper()}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.assessment_id


class ANCInvestigation(models.Model):
    class InvestigationStatus(models.TextChoices):
        ORDERED = "ORDERED", "Ordered"
        COLLECTED = "COLLECTED", "Sample Collected"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    investigation_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    pregnancy = models.ForeignKey(
        PregnancyRecord,
        on_delete=models.PROTECT,
        related_name="investigations",
    )

    anc_visit = models.ForeignKey(
        ANCVisit,
        on_delete=models.PROTECT,
        related_name="investigations",
        null=True,
        blank=True,
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="anc_investigations",
    )

    test_name = models.CharField(
        max_length=200,
    )

    test_code = models.CharField(
        max_length=50,
        blank=True,
    )

    ordered_at = models.DateTimeField(
        auto_now_add=True,
    )

    result = models.TextField(
        blank=True,
    )

    result_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    reference_range = models.CharField(
        max_length=255,
        blank=True,
    )

    abnormal = models.BooleanField(
        default=False,
    )

    status = models.CharField(
        max_length=30,
        choices=InvestigationStatus.choices,
        default=InvestigationStatus.ORDERED,
    )

    ordered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="anc_investigations_ordered",
    )

    notes = models.TextField(
        blank=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-ordered_at"]

    def save(self, *args, **kwargs):
        if not self.investigation_id:
            self.investigation_id = (
                f"ANC-LAB-{uuid.uuid4().hex[:12].upper()}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.investigation_id


class ANCReferral(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    class Urgency(models.TextChoices):
        ROUTINE = "ROUTINE", "Routine"
        URGENT = "URGENT", "Urgent"
        EMERGENCY = "EMERGENCY", "Emergency"

    referral_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    pregnancy = models.ForeignKey(
        PregnancyRecord,
        on_delete=models.PROTECT,
        related_name="referrals",
    )

    anc_visit = models.ForeignKey(
        ANCVisit,
        on_delete=models.PROTECT,
        related_name="referrals",
        null=True,
        blank=True,
    )

    from_facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="anc_referrals_sent",
    )

    to_facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="anc_referrals_received",
    )

    reason = models.TextField()

    clinical_summary = models.TextField(
        blank=True,
    )

    urgency = models.CharField(
        max_length=20,
        choices=Urgency.choices,
        default=Urgency.ROUTINE,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    referral_date = models.DateTimeField(
        auto_now_add=True,
    )

    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    referred_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="anc_referrals_created",
    )

    notes = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = ["-referral_date"]

    def save(self, *args, **kwargs):
        if not self.referral_id:
            self.referral_id = (
                f"ANC-REF-{uuid.uuid4().hex[:12].upper()}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.referral_id


class ANCClinicalEvent(models.Model):
    class EventType(models.TextChoices):
        REGISTERED = "REGISTERED", "Registered"
        PREGNANCY_CREATED = "PREGNANCY_CREATED", "Pregnancy Created"
        VISIT_COMPLETED = "VISIT_COMPLETED", "ANC Visit Completed"
        RISK_ASSESSED = "RISK_ASSESSED", "Risk Assessed"
        INVESTIGATION_ORDERED = "INVESTIGATION_ORDERED", "Investigation Ordered"
        INVESTIGATION_COMPLETED = "INVESTIGATION_COMPLETED", "Investigation Completed"
        REFERRAL_CREATED = "REFERRAL_CREATED", "Referral Created"
        REFERRAL_ACCEPTED = "REFERRAL_ACCEPTED", "Referral Accepted"
        REFERRAL_COMPLETED = "REFERRAL_COMPLETED", "Referral Completed"
        TRANSFERRED = "TRANSFERRED", "Transferred"
        CLOSED = "CLOSED", "Closed"

    event_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    pregnancy = models.ForeignKey(
        PregnancyRecord,
        on_delete=models.PROTECT,
        related_name="clinical_events",
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="anc_clinical_events",
    )

    event_type = models.CharField(
        max_length=40,
        choices=EventType.choices,
    )

    description = models.TextField(
        blank=True,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="anc_clinical_events",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["created_at"]

    def save(self, *args, **kwargs):
        if not self.event_id:
            self.event_id = (
                f"ANC-EVENT-{uuid.uuid4().hex[:12].upper()}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.event_id