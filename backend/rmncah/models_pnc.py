import uuid

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class PNCVisit(models.Model):
    class VisitType(models.TextChoices):
        IMMEDIATE = "IMMEDIATE", "Immediate Postnatal"
        DAY_1 = "DAY_1", "Day 1"
        DAY_2 = "DAY_2", "Day 2"
        DAY_3 = "DAY_3", "Day 3"
        WEEK_1 = "WEEK_1", "First Week"
        WEEK_2 = "WEEK_2", "Second Week"
        WEEK_6 = "WEEK_6", "Six Weeks"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        COMPLETED = "COMPLETED", "Completed"
        MISSED = "MISSED", "Missed"
        CANCELLED = "CANCELLED", "Cancelled"
        REFERRED = "REFERRED", "Referred"

    visit_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    pregnancy = models.ForeignKey(
        "rmncah.PregnancyRecord",
        on_delete=models.PROTECT,
        related_name="pnc_visits",
    )

    delivery = models.ForeignKey(
        "rmncah.DeliveryRecord",
        on_delete=models.PROTECT,
        related_name="pnc_visits",
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="pnc_visits",
    )

    visit_type = models.CharField(
        max_length=30,
        choices=VisitType.choices,
    )

    visit_date = models.DateTimeField()

    days_after_delivery = models.PositiveIntegerField(
        default=0,
    )

    temperature_c = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
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

    bleeding = models.BooleanField(
        default=False,
    )

    fever = models.BooleanField(
        default=False,
    )

    severe_headache = models.BooleanField(
        default=False,
    )

    visual_disturbance = models.BooleanField(
        default=False,
    )

    abdominal_pain = models.BooleanField(
        default=False,
    )

    foul_smelling_lochia = models.BooleanField(
        default=False,
    )

    breast_problem = models.BooleanField(
        default=False,
    )

    wound_problem = models.BooleanField(
        default=False,
    )

    mental_health_concern = models.BooleanField(
        default=False,
    )

    breastfeeding_status = models.CharField(
        max_length=100,
        blank=True,
    )

    maternal_condition = models.TextField(
        blank=True,
    )

    clinical_assessment = models.TextField(
        blank=True,
    )

    treatment_given = models.TextField(
        blank=True,
    )

    counselling = models.TextField(
        blank=True,
    )

    family_planning_counselling = models.TextField(
        blank=True,
    )

    referral_required = models.BooleanField(
        default=False,
    )

    referral_reason = models.TextField(
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
        related_name="pnc_visits_attended",
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def save(self, *args, **kwargs):
        if not self.visit_id:
            self.visit_id = (
                f"PNC-{uuid.uuid4().hex[:12].upper()}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.visit_id


class NewbornCareRecord(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        REFERRED = "REFERRED", "Referred"
        DISCHARGED = "DISCHARGED", "Discharged"
        DECEASED = "DECEASED", "Deceased"

    record_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    newborn = models.ForeignKey(
        "rmncah.NewbornRecord",
        on_delete=models.PROTECT,
        related_name="care_records",
    )

    pregnancy = models.ForeignKey(
        "rmncah.PregnancyRecord",
        on_delete=models.PROTECT,
        related_name="newborn_care_records",
    )

    delivery = models.ForeignKey(
        "rmncah.DeliveryRecord",
        on_delete=models.PROTECT,
        related_name="newborn_care_records",
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="newborn_care_records",
    )

    assessment_date = models.DateTimeField()

    age_days = models.PositiveIntegerField(
        default=0,
    )

    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
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

    heart_rate = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    feeding_method = models.CharField(
        max_length=100,
        blank=True,
    )

    feeding_well = models.BooleanField(
        null=True,
        blank=True,
    )

    jaundice_present = models.BooleanField(
        default=False,
    )

    difficulty_breathing = models.BooleanField(
        default=False,
    )

    fever = models.BooleanField(
        default=False,
    )

    hypothermia = models.BooleanField(
        default=False,
    )

    convulsions = models.BooleanField(
        default=False,
    )

    lethargy = models.BooleanField(
        default=False,
    )

    umbilical_problem = models.BooleanField(
        default=False,
    )

    skin_condition = models.TextField(
        blank=True,
    )

    elimination_status = models.TextField(
        blank=True,
    )

    clinical_assessment = models.TextField(
        blank=True,
    )

    treatment_given = models.TextField(
        blank=True,
    )

    immunisation_given = models.TextField(
        blank=True,
    )

    vitamin_supplementation = models.TextField(
        blank=True,
    )

    referral_required = models.BooleanField(
        default=False,
    )

    referral_reason = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="newborn_care_records_reviewed",
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def save(self, *args, **kwargs):
        if not self.record_id:
            self.record_id = (
                f"NBC-{uuid.uuid4().hex[:12].upper()}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.record_id


class PNCReferral(models.Model):
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
        "rmncah.PregnancyRecord",
        on_delete=models.PROTECT,
        related_name="pnc_referrals",
    )

    newborn = models.ForeignKey(
        "rmncah.NewbornRecord",
        on_delete=models.PROTECT,
        related_name="pnc_referrals",
        null=True,
        blank=True,
    )

    from_facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="pnc_referrals_sent",
    )

    to_facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="pnc_referrals_received",
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

    referred_at = models.DateTimeField(
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
        related_name="pnc_referrals_created",
    )

    notes = models.TextField(
        blank=True,
    )

    def save(self, *args, **kwargs):
        if not self.referral_id:
            self.referral_id = (
                f"PNC-REF-{uuid.uuid4().hex[:12].upper()}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.referral_id


class PNCFollowUp(models.Model):
    class FollowUpType(models.TextChoices):
        MATERNAL = "MATERNAL", "Maternal"
        NEWBORN = "NEWBORN", "Newborn"
        BOTH = "BOTH", "Mother and Newborn"

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        COMPLETED = "COMPLETED", "Completed"
        MISSED = "MISSED", "Missed"
        CANCELLED = "CANCELLED", "Cancelled"

    followup_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    pregnancy = models.ForeignKey(
        "rmncah.PregnancyRecord",
        on_delete=models.PROTECT,
        related_name="pnc_followups",
    )

    newborn = models.ForeignKey(
        "rmncah.NewbornRecord",
        on_delete=models.PROTECT,
        related_name="pnc_followups",
        null=True,
        blank=True,
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="pnc_followups",
    )

    followup_type = models.CharField(
        max_length=20,
        choices=FollowUpType.choices,
    )

    scheduled_date = models.DateField()

    purpose = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pnc_followups_completed",
        null=True,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pnc_followups_created",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def save(self, *args, **kwargs):
        if not self.followup_id:
            self.followup_id = (
                f"PNC-FU-{uuid.uuid4().hex[:12].upper()}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.followup_id