import uuid

from django.db import models


class Donor(models.Model):

    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"
        NOT_STATED = "NOT_STATED", "Prefer not to state"

    class DonorStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        TEMPORARILY_DEFERRED = (
            "TEMPORARILY_DEFERRED",
            "Temporarily Deferred",
        )
        PERMANENTLY_DEFERRED = (
            "PERMANENTLY_DEFERRED",
            "Permanently Deferred",
        )
        INACTIVE = "INACTIVE", "Inactive"

    donor_id = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
    )

    national_id = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
    )

    first_name = models.CharField(
        max_length=100,
    )

    middle_name = models.CharField(
        max_length=100,
        blank=True,
    )

    last_name = models.CharField(
        max_length=100,
    )

    date_of_birth = models.DateField()

    gender = models.CharField(
        max_length=20,
        choices=Gender.choices,
    )

    phone = models.CharField(
        max_length=30,
    )

    email = models.EmailField(
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    emergency_contact_name = models.CharField(
        max_length=200,
        blank=True,
    )

    emergency_contact_phone = models.CharField(
        max_length=30,
        blank=True,
    )

    blood_group = models.CharField(
        max_length=10,
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=DonorStatus.choices,
        default=DonorStatus.ACTIVE,
    )

    registered_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    notes = models.TextField(
        blank=True,
    )

    def save(self, *args, **kwargs):

        if not self.donor_id:
            self.donor_id = (
                f"DON-{uuid.uuid4().hex[:10].upper()}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.donor_id} - "
            f"{self.first_name} {self.last_name}"
        )

class Donation(models.Model):

    class DonationType(models.TextChoices):
        WHOLE_BLOOD = (
            "WHOLE_BLOOD",
            "Whole Blood",
        )
        APHERESIS = (
            "APHERESIS",
            "Apheresis",
        )

    class DonationStatus(models.TextChoices):
        REGISTERED = "REGISTERED", "Registered"
        COLLECTED = "COLLECTED", "Collected"
        TESTING = "TESTING", "Testing"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        COMPLETED = "COMPLETED", "Completed"

    donation_id = models.CharField(
        max_length=40,
        unique=True,
        editable=False,
    )

    donor = models.ForeignKey(
        Donor,
        on_delete=models.PROTECT,
        related_name="donations",
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="donations",
    )

    donation_type = models.CharField(
        max_length=30,
        choices=DonationType.choices,
        default=DonationType.WHOLE_BLOOD,
    )

    collection_date = models.DateTimeField()

    volume_ml = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=DonationStatus.choices,
        default=DonationStatus.REGISTERED,
    )

    collection_notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def save(self, *args, **kwargs):

        if not self.donation_id:
            self.donation_id = (
                f"DONATION-{uuid.uuid4().hex[:10].upper()}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.donation_id

class DonorEligibility(models.Model):

    class Decision(models.TextChoices):
        ELIGIBLE = "ELIGIBLE", "Eligible"
        DEFERRED = "DEFERRED", "Deferred"
        PENDING = "PENDING", "Pending"

    donor = models.ForeignKey(
        Donor,
        on_delete=models.PROTECT,
        related_name="eligibility_assessments",
    )

    assessment_date = models.DateTimeField(
        auto_now_add=True,
    )

    decision = models.CharField(
        max_length=20,
        choices=Decision.choices,
        default=Decision.PENDING,
    )

    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    haemoglobin = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    blood_pressure = models.CharField(
        max_length=30,
        blank=True,
    )

    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
    )

    screening_notes = models.TextField(
        blank=True,
    )

    assessed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="donor_eligibility_assessments",
    )

    def __str__(self):
        return (
            f"{self.donor.donor_id} - "
            f"{self.decision}"
        )

class DeferralRecord(models.Model):

    class DeferralType(models.TextChoices):
        TEMPORARY = "TEMPORARY", "Temporary"
        PERMANENT = "PERMANENT", "Permanent"

    donor = models.ForeignKey(
        Donor,
        on_delete=models.PROTECT,
        related_name="deferrals",
    )

    deferral_type = models.CharField(
        max_length=20,
        choices=DeferralType.choices,
    )

    reason = models.TextField()

    start_date = models.DateField()

    end_date = models.DateField(
        null=True,
        blank=True,
    )

    recorded_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="donor_deferrals",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"{self.donor.donor_id} - "
            f"{self.deferral_type}"
        )

class BloodSample(models.Model):

    class SampleStatus(models.TextChoices):
        COLLECTED = "COLLECTED", "Collected"
        RECEIVED = "RECEIVED", "Received"
        TESTING = "TESTING", "Testing"
        COMPLETED = "COMPLETED", "Completed"
        REJECTED = "REJECTED", "Rejected"

    sample_id = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
    )

    donation = models.OneToOneField(
        Donation,
        on_delete=models.PROTECT,
        related_name="blood_sample",
    )

    collected_at = models.DateTimeField()

    received_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=SampleStatus.choices,
        default=SampleStatus.COLLECTED,
    )

    collection_notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def save(self, *args, **kwargs):

        if not self.sample_id:
            self.sample_id = (
                f"SAMPLE-{uuid.uuid4().hex[:10].upper()}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.sample_id

class LaboratoryTest(models.Model):

    class TestType(models.TextChoices):
        ABO_GROUPING = (
            "ABO_GROUPING",
            "ABO Blood Grouping",
        )
        RH_TYPING = (
            "RH_TYPING",
            "Rh Typing",
        )
        HIV = (
            "HIV",
            "HIV Screening",
        )
        HEPATITIS_B = (
            "HEPATITIS_B",
            "Hepatitis B Screening",
        )
        HEPATITIS_C = (
            "HEPATITIS_C",
            "Hepatitis C Screening",
        )
        SYPHILIS = (
            "SYPHILIS",
            "Syphilis Screening",
        )
        OTHER = (
            "OTHER",
            "Other",
        )

    class TestStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        INVALID = "INVALID", "Invalid"

    test_id = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
    )

    sample = models.ForeignKey(
        BloodSample,
        on_delete=models.PROTECT,
        related_name="laboratory_tests",
    )

    test_type = models.CharField(
        max_length=50,
        choices=TestType.choices,
    )

    status = models.CharField(
        max_length=30,
        choices=TestStatus.choices,
        default=TestStatus.PENDING,
    )

    result = models.CharField(
        max_length=100,
        blank=True,
    )

    result_notes = models.TextField(
        blank=True,
    )

    performed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="laboratory_tests_performed",
    )

    performed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def save(self, *args, **kwargs):

        if not self.test_id:
            self.test_id = (
                f"TEST-{uuid.uuid4().hex[:10].upper()}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.test_id} - "
            f"{self.get_test_type_display()}"
        )

class BloodUnit(models.Model):

    class Status(models.TextChoices):
        COLLECTED = "COLLECTED", "Collected"
        QUARANTINED = "QUARANTINED", "Quarantined"
        TESTING = "TESTING", "Testing"
        RELEASED = "RELEASED", "Released"
        RESERVED = "RESERVED", "Reserved"
        DISPATCHED = "DISPATCHED", "Dispatched"
        TRANSFUSED = "TRANSFUSED", "Transfused"
        EXPIRED = "EXPIRED", "Expired"
        DISCARDED = "DISCARDED", "Discarded"

    unit_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    donation = models.ForeignKey(
        Donation,
        on_delete=models.PROTECT,
        related_name="blood_units",
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="blood_units",
    )

    blood_group = models.CharField(
        max_length=10,
    )

    component_type = models.CharField(
        max_length=100,
        default="Whole Blood",
    )

    volume_ml = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    collection_date = models.DateTimeField()

    expiry_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.QUARANTINED,
    )

    barcode = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
    )

    storage_location = models.CharField(
        max_length=100,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def save(self, *args, **kwargs):

        if not self.unit_id:
            self.unit_id = (
                f"UNIT-{uuid.uuid4().hex[:12].upper()}"
            )

        if not self.barcode:
            self.barcode = self.unit_id

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.unit_id} - "
            f"{self.blood_group} - "
            f"{self.component_type}"
        )