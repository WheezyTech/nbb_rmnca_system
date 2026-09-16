import uuid

from django.db import models


class StorageLocation(models.Model):

    class StorageType(models.TextChoices):
        REFRIGERATOR = "REFRIGERATOR", "Blood Refrigerator"
        FREEZER = "FREEZER", "Plasma Freezer"
        PLATELET = "PLATELET", "Platelet Incubator"
        OTHER = "OTHER", "Other"

    location_id = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="storage_locations",
    )

    name = models.CharField(
        max_length=150,
    )

    storage_type = models.CharField(
        max_length=30,
        choices=StorageType.choices,
    )

    temperature_min = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    temperature_max = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def save(self, *args, **kwargs):

        if not self.location_id:
            self.location_id = (
                f"STORAGE-{uuid.uuid4().hex[:10].upper()}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.facility.name} - {self.name}"

class InventoryRecord(models.Model):

    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        RESERVED = "RESERVED", "Reserved"
        ISSUED = "ISSUED", "Issued"
        TRANSFERRED = "TRANSFERRED", "Transferred"
        TRANSFUSED = "TRANSFUSED", "Transfused"
        EXPIRED = "EXPIRED", "Expired"
        DISCARDED = "DISCARDED", "Discarded"

    inventory_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    blood_unit = models.OneToOneField(
        "donors.BloodUnit",
        on_delete=models.PROTECT,
        related_name="inventory_record",
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="inventory_records",
    )

    storage_location = models.ForeignKey(
        StorageLocation,
        on_delete=models.PROTECT,
        related_name="inventory_records",
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )

    received_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def save(self, *args, **kwargs):

        if not self.inventory_id:
            self.inventory_id = (
                f"INV-{uuid.uuid4().hex[:12].upper()}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.inventory_id

class BloodReservation(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        FULFILLED = "FULFILLED", "Fulfilled"
        CANCELLED = "CANCELLED", "Cancelled"
        EXPIRED = "EXPIRED", "Expired"

    reservation_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    inventory = models.ForeignKey(
        InventoryRecord,
        on_delete=models.PROTECT,
        related_name="reservations",
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="blood_reservations",
    )

    patient_reference = models.CharField(
        max_length=100,
        blank=True,
    )

    blood_group = models.CharField(
        max_length=10,
    )

    reserved_at = models.DateTimeField(
        auto_now_add=True,
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    notes = models.TextField(
        blank=True,
    )

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="blood_reservations_created",
    )

    def save(self, *args, **kwargs):

        if not self.reservation_id:
            self.reservation_id = (
                f"RES-{uuid.uuid4().hex[:12].upper()}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.reservation_id

class BloodRequest(models.Model):

    class Priority(models.TextChoices):
        ROUTINE = "ROUTINE", "Routine"
        URGENT = "URGENT", "Urgent"
        EMERGENCY = "EMERGENCY", "Emergency"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        REVIEWED = "REVIEWED", "Reviewed"
        PARTIALLY_FULFILLED = (
            "PARTIALLY_FULFILLED",
            "Partially Fulfilled",
        )
        FULFILLED = "FULFILLED", "Fulfilled"
        CANCELLED = "CANCELLED", "Cancelled"
        REJECTED = "REJECTED", "Rejected"

    request_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="blood_requests",
    )

    patient_reference = models.CharField(
        max_length=100,
    )

    clinical_reference = models.CharField(
        max_length=100,
        blank=True,
    )

    blood_group = models.CharField(
        max_length=10,
    )

    component_type = models.CharField(
        max_length=100,
    )

    requested_units = models.PositiveIntegerField()

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.ROUTINE,
    )

    clinical_indication = models.TextField(
        blank=True,
    )

    required_by = models.DateTimeField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
    )

    requested_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="blood_requests_created",
    )

    reviewed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="blood_requests_reviewed",
        null=True,
        blank=True,
    )

    reviewed_at = models.DateTimeField(
        null=True,
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

        if not self.request_id:
            self.request_id = (
                f"REQ-{uuid.uuid4().hex[:12].upper()}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.request_id
    
class BloodIssue(models.Model):

    class IssueStatus(models.TextChoices):
        ISSUED = "ISSUED", "Issued"
        RETURNED = "RETURNED", "Returned"
        TRANSFUSED = "TRANSFUSED", "Transfused"
        CANCELLED = "CANCELLED", "Cancelled"

    issue_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    inventory = models.ForeignKey(
        InventoryRecord,
        on_delete=models.PROTECT,
        related_name="issues",
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="blood_issues",
    )

    patient_reference = models.CharField(
        max_length=100,
        blank=True,
    )

    clinical_reference = models.CharField(
        max_length=100,
        blank=True,
    )

    issued_at = models.DateTimeField(
        auto_now_add=True,
    )

    status = models.CharField(
        max_length=30,
        choices=IssueStatus.choices,
        default=IssueStatus.ISSUED,
    )

    issued_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="blood_issues_created",
    )

    notes = models.TextField(
        blank=True,
    )

    def save(self, *args, **kwargs):

        if not self.issue_id:
            self.issue_id = (
                f"ISSUE-{uuid.uuid4().hex[:12].upper()}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.issue_id

class BloodTransfer(models.Model):

    class Status(models.TextChoices):
        REQUESTED = "REQUESTED", "Requested"
        APPROVED = "APPROVED", "Approved"
        DISPATCHED = "DISPATCHED", "Dispatched"
        RECEIVED = "RECEIVED", "Received"
        CANCELLED = "CANCELLED", "Cancelled"

    transfer_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    blood_unit = models.ForeignKey(
        "donors.BloodUnit",
        on_delete=models.PROTECT,
        related_name="transfers",
    )

    from_facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="outgoing_blood_transfers",
    )

    to_facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="incoming_blood_transfers",
    )

    requested_at = models.DateTimeField(
        auto_now_add=True,
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    dispatched_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    received_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    rejected_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.REQUESTED,
    )

    requested_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="blood_transfers_requested",
    )

    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="blood_transfers_approved",
        null=True,
        blank=True,
    )

    rejected_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="blood_transfers_rejected",
        null=True,
        blank=True,
    )

    dispatched_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="blood_transfers_dispatched",
        null=True,
        blank=True,
    )

    received_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="blood_transfers_received",
        null=True,
        blank=True,
    )

    rejection_reason = models.TextField(
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    def save(self, *args, **kwargs):

        if not self.transfer_id:
            self.transfer_id = (
                f"TRANSFER-{uuid.uuid4().hex[:10].upper()}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.transfer_id

class InventoryMovement(models.Model):

    class MovementType(models.TextChoices):
        RECEIVED = "RECEIVED", "Received"
        MOVED = "MOVED", "Moved"
        RESERVED = "RESERVED", "Reserved"
        RELEASED = "RELEASED", "Released"
        ISSUED = "ISSUED", "Issued"
        RETURNED = "RETURNED", "Returned"
        TRANSFERRED = "TRANSFERRED", "Transferred"
        DISCARDED = "DISCARDED", "Discarded"
        EXPIRED = "EXPIRED", "Expired"

    movement_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    inventory = models.ForeignKey(
        InventoryRecord,
        on_delete=models.PROTECT,
        related_name="movements",
    )

    movement_type = models.CharField(
        max_length=30,
        choices=MovementType.choices,
    )

    from_location = models.ForeignKey(
        StorageLocation,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movements_from",
    )

    to_location = models.ForeignKey(
        StorageLocation,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movements_to",
    )

    reason = models.TextField(
        blank=True,
    )

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="inventory_movements_created",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def save(self, *args, **kwargs):

        if not self.movement_id:
            self.movement_id = (
                f"MOVE-{uuid.uuid4().hex[:12].upper()}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.movement_id

class InventoryAlert(models.Model):

    class AlertLevel(models.TextChoices):
        ZERO_STOCK = "ZERO_STOCK", "Zero Stock"
        CRITICAL = "CRITICAL", "Critical"
        LOW = "LOW", "Low"

    class AlertStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ACKNOWLEDGED = "ACKNOWLEDGED", "Acknowledged"
        RESOLVED = "RESOLVED", "Resolved"

    alert_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="inventory_alerts",
    )

    blood_group = models.CharField(
        max_length=10,
    )

    component_type = models.CharField(
        max_length=50,
    )

    available_units = models.PositiveIntegerField(
        default=0,
    )

    alert_level = models.CharField(
        max_length=30,
        choices=AlertLevel.choices,
    )

    status = models.CharField(
        max_length=30,
        choices=AlertStatus.choices,
        default=AlertStatus.ACTIVE,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    acknowledged_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="inventory_alerts_acknowledged",
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    resolved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="inventory_alerts_resolved",
    )

    resolution_notes = models.TextField(
        blank=True,
    )

    last_checked_at = models.DateTimeField(
        auto_now=True,
    )

    def save(self, *args, **kwargs):

        if not self.alert_id:
            self.alert_id = (
                f"ALERT-{uuid.uuid4().hex[:12].upper()}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.alert_id} - "
            f"{self.facility.name} - "
            f"{self.blood_group}"
        )

class BloodStockAlert(models.Model):

    class AlertLevel(models.TextChoices):
        LOW = "LOW", "Low Stock"
        CRITICAL = "CRITICAL", "Critical Stock"
        ZERO_STOCK = "ZERO_STOCK", "Zero Stock"

    class AlertStatus(models.TextChoices):
        OPEN = "OPEN", "Open"
        ACKNOWLEDGED = "ACKNOWLEDGED", "Acknowledged"
        RESOLVED = "RESOLVED", "Resolved"

    alert_id = models.CharField(
        max_length=60,
        unique=True,
        editable=False,
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="blood_stock_alerts",
    )

    blood_group = models.CharField(
        max_length=10,
    )

    component_type = models.CharField(
        max_length=50,
    )

    available_units = models.PositiveIntegerField(
        default=0,
    )

    alert_level = models.CharField(
        max_length=20,
        choices=AlertLevel.choices,
    )

    status = models.CharField(
        max_length=20,
        choices=AlertStatus.choices,
        default=AlertStatus.OPEN,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    acknowledged_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="blood_stock_alerts_acknowledged",
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    resolved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="blood_stock_alerts_resolved",
    )

    resolution_notes = models.TextField(
        blank=True,
    )

    def save(self, *args, **kwargs):

        if not self.alert_id:
            self.alert_id = (
                f"ALERT-{uuid.uuid4().hex[:12].upper()}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.facility.name} - "
            f"{self.blood_group} - "
            f"{self.component_type} - "
            f"{self.alert_level}"
        )


from .models_clinical import (
    BloodRequestFulfillment,
    BloodRequestEvent,
)