import uuid

from django.db import models


class BloodRequestFulfillment(models.Model):
    class Status(models.TextChoices):
        RESERVED = "RESERVED", "Reserved"
        ISSUED = "ISSUED", "Issued"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    fulfillment_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    blood_request = models.ForeignKey(
        "inventory.BloodRequest",
        on_delete=models.PROTECT,
        related_name="fulfillments",
    )

    inventory = models.ForeignKey(
        "inventory.InventoryRecord",
        on_delete=models.PROTECT,
        related_name="request_fulfillments",
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.RESERVED,
    )

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="blood_request_fulfillments_created",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.fulfillment_id:
            self.fulfillment_id = (
                f"FUL-{uuid.uuid4().hex[:12].upper()}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.fulfillment_id


class BloodRequestEvent(models.Model):
    class EventType(models.TextChoices):
        CREATED = "CREATED", "Created"
        REVIEWED = "REVIEWED", "Reviewed"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"
        MATCHED = "MATCHED", "Matched"
        PARTIALLY_FULFILLED = (
            "PARTIALLY_FULFILLED",
            "Partially Fulfilled",
        )
        FULFILLED = "FULFILLED", "Fulfilled"
        RESERVATION_CREATED = (
            "RESERVATION_CREATED",
            "Reservation Created",
        )
        BLOOD_ISSUED = "BLOOD_ISSUED", "Blood Issued"
        BLOOD_RETURNED = "BLOOD_RETURNED", "Blood Returned"
        TRANSFUSED = "TRANSFUSED", "Transfused"

    event_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    blood_request = models.ForeignKey(
        "inventory.BloodRequest",
        on_delete=models.PROTECT,
        related_name="events",
    )

    event_type = models.CharField(
        max_length=40,
        choices=EventType.choices,
    )

    performed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="blood_request_events",
    )

    description = models.TextField(blank=True)

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.event_id:
            self.event_id = (
                f"REQEVENT-{uuid.uuid4().hex[:12].upper()}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.event_id


class TransfusionReaction(models.Model):

    class Severity(models.TextChoices):
        MILD = "MILD", "Mild"
        MODERATE = "MODERATE", "Moderate"
        SEVERE = "SEVERE", "Severe"
        LIFE_THREATENING = (
            "LIFE_THREATENING",
            "Life Threatening",
        )
        FATAL = "FATAL", "Fatal"

    class ReactionType(models.TextChoices):
        FEBRILE = "FEBRILE", "Febrile Reaction"
        ALLERGIC = "ALLERGIC", "Allergic Reaction"
        HEMOLYTIC = "HEMOLYTIC", "Hemolytic Reaction"
        ANAPHYLACTIC = (
            "ANAPHYLACTIC",
            "Anaphylactic Reaction",
        )
        TRALI = "TRALI", "TRALI"
        TACO = "TACO", "TACO"
        SEPSIS = "SEPSIS", "Septic Reaction"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        REPORTED = "REPORTED", "Reported"
        UNDER_INVESTIGATION = (
            "UNDER_INVESTIGATION",
            "Under Investigation",
        )
        CONFIRMED = "CONFIRMED", "Confirmed"
        RULED_OUT = "RULED_OUT", "Ruled Out"
        CLOSED = "CLOSED", "Closed"

    reaction_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    blood_issue = models.ForeignKey(
        "inventory.BloodIssue",
        on_delete=models.PROTECT,
        related_name="transfusion_reactions",
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="transfusion_reactions",
    )

    patient_reference = models.CharField(
        max_length=100,
    )

    reaction_type = models.CharField(
        max_length=30,
        choices=ReactionType.choices,
    )

    severity = models.CharField(
        max_length=30,
        choices=Severity.choices,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.REPORTED,
    )

    symptoms = models.TextField(
        blank=True,
    )

    reaction_date = models.DateTimeField()

    reported_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="transfusion_reactions_reported",
    )

    clinical_action = models.TextField(
        blank=True,
    )

    investigation_findings = models.TextField(
        blank=True,
    )

    laboratory_findings = models.TextField(
        blank=True,
    )

    outcome = models.TextField(
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

        if not self.reaction_id:
            self.reaction_id = (
                f"REACTION-{uuid.uuid4().hex[:12].upper()}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.reaction_id