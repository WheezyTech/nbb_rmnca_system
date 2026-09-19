import uuid

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class DeliveryRecord(models.Model):
    class DeliveryMode(models.TextChoices):
        SPONTANEOUS_VAGINAL = "SVD", "Spontaneous Vaginal Delivery"
        ASSISTED_VAGINAL = "AVD", "Assisted Vaginal Delivery"
        CAESAREAN_SECTION = "CS", "Caesarean Section"
        BREECH = "BREECH", "Breech Delivery"
        OTHER = "OTHER", "Other"

    class DeliveryStatus(models.TextChoices):
        COMPLETED = "COMPLETED", "Completed"
        COMPLICATION = "COMPLICATION", "Complication"
        REFERRED = "REFERRED", "Referred"

    delivery_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    pregnancy = models.OneToOneField(
        "rmncah.PregnancyRecord",
        on_delete=models.PROTECT,
        related_name="delivery",
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="deliveries",
    )

    delivery_date = models.DateTimeField()

    delivery_mode = models.CharField(
        max_length=20,
        choices=DeliveryMode.choices,
    )

    delivery_status = models.CharField(
        max_length=30,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.COMPLETED,
    )

    gestational_age_weeks = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MaxValueValidator(45)],
    )

    number_of_babies = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )

    attended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="deliveries_attended",
    )

    indication_for_caesarean = models.TextField(
        blank=True,
    )

    complications = models.TextField(
        blank=True,
    )

    estimated_blood_loss_ml = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    placenta_complete = models.BooleanField(
        null=True,
        blank=True,
    )

    maternal_condition = models.TextField(
        blank=True,
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
        if not self.delivery_id:
            self.delivery_id = (
                f"DEL-{uuid.uuid4().hex[:12].upper()}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.delivery_id


class NewbornRecord(models.Model):
    class Sex(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        AMBIGUOUS = "AMBIGUOUS", "Ambiguous"
        UNKNOWN = "UNKNOWN", "Unknown"

    class Condition(models.TextChoices):
        GOOD = "GOOD", "Good"
        FAIR = "FAIR", "Fair"
        CRITICAL = "CRITICAL", "Critical"
        DECEASED = "DECEASED", "Deceased"

    class Status(models.TextChoices):
        ALIVE = "ALIVE", "Alive"
        STILLBIRTH = "STILLBIRTH", "Stillbirth"
        NEONATAL_DEATH = "NEONATAL_DEATH", "Neonatal Death"

    newborn_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    delivery = models.ForeignKey(
        DeliveryRecord,
        on_delete=models.PROTECT,
        related_name="newborns",
    )

    pregnancy = models.ForeignKey(
        "rmncah.PregnancyRecord",
        on_delete=models.PROTECT,
        related_name="newborns",
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="newborn_records",
    )

    birth_order = models.PositiveIntegerField(
        default=1,
    )

    sex = models.CharField(
        max_length=20,
        choices=Sex.choices,
    )

    date_time_of_birth = models.DateTimeField()

    birth_weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )

    length_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    head_circumference_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    apgar_one_minute = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MaxValueValidator(10)],
    )

    apgar_five_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MaxValueValidator(10)],
    )

    apgar_ten_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MaxValueValidator(10)],
    )

    condition = models.CharField(
        max_length=20,
        choices=Condition.choices,
        default=Condition.GOOD,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.ALIVE,
    )

    resuscitation_required = models.BooleanField(
        default=False,
    )

    resuscitation_details = models.TextField(
        blank=True,
    )

    immediate_care = models.TextField(
        blank=True,
    )

    transferred_to_nicu = models.BooleanField(
        default=False,
    )

    nicu_reason = models.TextField(
        blank=True,
    )

    complications = models.TextField(
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="newborns_recorded",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["date_time_of_birth"]
        constraints = [
            models.UniqueConstraint(
                fields=["delivery", "birth_order"],
                name="unique_birth_order_per_delivery",
            )
        ]

    def save(self, *args, **kwargs):
        if not self.newborn_id:
            self.newborn_id = (
                f"NB-{uuid.uuid4().hex[:12].upper()}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.newborn_id


class LabourRecord(models.Model):
    class Status(models.TextChoices):
        ADMITTED = "ADMITTED", "Admitted"
        ACTIVE = "ACTIVE", "Active Labour"
        DELIVERED = "DELIVERED", "Delivered"
        REFERRED = "REFERRED", "Referred"
        CLOSED = "CLOSED", "Closed"

    labour_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    pregnancy = models.OneToOneField(
        "rmncah.PregnancyRecord",
        on_delete=models.PROTECT,
        related_name="labour",
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="labour_records",
    )

    admission_date = models.DateTimeField()

    labour_onset_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    cervical_dilation_cm = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
    )

    contractions_per_10_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    membrane_status = models.CharField(
        max_length=100,
        blank=True,
    )

    liquor_character = models.CharField(
        max_length=100,
        blank=True,
    )

    fetal_presentation = models.CharField(
        max_length=100,
        blank=True,
    )

    fetal_position = models.CharField(
        max_length=100,
        blank=True,
    )

    fetal_heart_rate = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    maternal_bp_systolic = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    maternal_bp_diastolic = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    maternal_pulse = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    maternal_temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ADMITTED,
    )

    complications = models.TextField(
        blank=True,
    )

    management_plan = models.TextField(
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    managed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="labour_records_managed",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def save(self, *args, **kwargs):
        if not self.labour_id:
            self.labour_id = (
                f"LAB-{uuid.uuid4().hex[:12].upper()}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.labour_id


class PostnatalMotherRecord(models.Model):
    class Status(models.TextChoices):
        STABLE = "STABLE", "Stable"
        COMPLICATION = "COMPLICATION", "Complication"
        REFERRED = "REFERRED", "Referred"
        DISCHARGED = "DISCHARGED", "Discharged"

    postnatal_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    pregnancy = models.ForeignKey(
        "rmncah.PregnancyRecord",
        on_delete=models.PROTECT,
        related_name="postnatal_maternal_records",
    )

    delivery = models.ForeignKey(
        DeliveryRecord,
        on_delete=models.PROTECT,
        related_name="postnatal_records",
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="postnatal_mothers",
    )

    assessment_date = models.DateTimeField()

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

    breast_condition = models.TextField(
        blank=True,
    )

    uterine_involution = models.TextField(
        blank=True,
    )

    lochia = models.TextField(
        blank=True,
    )

    wound_condition = models.TextField(
        blank=True,
    )

    mental_health_observation = models.TextField(
        blank=True,
    )

    breastfeeding_status = models.CharField(
        max_length=100,
        blank=True,
    )

    complications = models.TextField(
        blank=True,
    )

    clinical_assessment = models.TextField(
        blank=True,
    )

    plan = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.STABLE,
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="postnatal_mothers_reviewed",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def save(self, *args, **kwargs):
        if not self.postnatal_id:
            self.postnatal_id = (
                f"PNM-{uuid.uuid4().hex[:12].upper()}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.postnatal_id