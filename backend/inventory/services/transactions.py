from django.db import transaction
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from inventory.models import (
    InventoryRecord,
    BloodReservation,
    BloodIssue,
    BloodTransfer,
    InventoryMovement,
)


def create_inventory_record(
    blood_unit,
    facility,
    storage_location,
    created_by,
):
    """
    Create an inventory record for a newly collected
    blood unit.

    New units enter quarantine by default.
    """

    if blood_unit.facility_id != facility.id:
        raise ValidationError(
            "Blood unit does not belong to this facility."
        )

    if storage_location.facility_id != facility.id:
        raise ValidationError(
            "Storage location does not belong to this facility."
        )

    with transaction.atomic():

        inventory, created = (
            InventoryRecord.objects.get_or_create(
                blood_unit=blood_unit,
                defaults={
                    "facility": facility,
                    "storage_location": storage_location,
                    "status": InventoryRecord.Status.QUARANTINED,
                },
            )
        )

        if not created:
            raise ValidationError(
                "This blood unit already has an inventory record."
            )

        InventoryMovement.objects.create(
            inventory=inventory,
            movement_type=(
                InventoryMovement.MovementType.RECEIVED
            ),
            to_location=storage_location,
            reason="Blood unit received into inventory.",
            created_by=created_by,
        )

        return inventory

@transaction.atomic
def release_inventory(
    inventory_id,
    released_by,
):
    """
    Release a quarantined blood unit into available stock.
    """

    inventory = (
        InventoryRecord.objects
        .select_for_update()
        .select_related(
            "blood_unit",
            "storage_location",
        )
        .get(
            pk=inventory_id
        )
    )

    if inventory.status != (
        InventoryRecord.Status.QUARANTINED
    ):
        raise ValidationError(
            "Only quarantined blood units can be released."
        )

    inventory.status = (
        InventoryRecord.Status.AVAILABLE
    )

    inventory.blood_unit.status = "RELEASED"

    inventory.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    inventory.blood_unit.save(
        update_fields=["status"]
    )

    InventoryMovement.objects.create(
        inventory=inventory,
        movement_type=(
            InventoryMovement.MovementType.RELEASED
        ),
        to_location=inventory.storage_location,
        reason="Blood unit released after approved screening.",
        created_by=released_by,
    )

    return inventory

@transaction.atomic
def reserve_blood(
    inventory_id,
    facility,
    created_by,
    patient_reference="",
    blood_group="",
    expires_at=None,
    notes="",
):
    """
    Reserve an available blood unit.
    """

    inventory = (
        InventoryRecord.objects
        .select_for_update()
        .select_related(
            "blood_unit",
        )
        .get(
            pk=inventory_id
        )
    )

    if inventory.facility_id != facility.id:
        raise ValidationError(
            "This blood unit does not belong to your facility."
        )

    if inventory.status != (
        InventoryRecord.Status.AVAILABLE
    ):
        raise ValidationError(
            "Only available blood can be reserved."
        )

    unit = inventory.blood_unit

    if unit.expiry_date:
        if unit.expiry_date <= timezone.now():
            inventory.status = (
                InventoryRecord.Status.EXPIRED
            )
            inventory.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            raise ValidationError(
                "This blood unit has expired."
            )

    if blood_group and unit.blood_group != blood_group:
        raise ValidationError(
            "Blood group does not match the requested group."
        )

    reservation = BloodReservation.objects.create(
        inventory=inventory,
        facility=facility,
        patient_reference=patient_reference,
        blood_group=unit.blood_group,
        expires_at=expires_at,
        status=BloodReservation.Status.ACTIVE,
        notes=notes,
        created_by=created_by,
    )

    inventory.status = (
        InventoryRecord.Status.RESERVED
    )

    inventory.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    InventoryMovement.objects.create(
        inventory=inventory,
        movement_type=(
            InventoryMovement.MovementType.RESERVED
        ),
        to_location=inventory.storage_location,
        reason=(
            f"Blood unit reserved. "
            f"Reservation: {reservation.reservation_id}"
        ),
        created_by=created_by,
    )

    return reservation

@transaction.atomic
def release_reservation(
    reservation_id,
    released_by,
):
    """
    Cancel an active reservation and return the unit
    to available stock.
    """

    reservation = (
        BloodReservation.objects
        .select_for_update()
        .select_related(
            "inventory",
            "inventory__blood_unit",
            "inventory__storage_location",
        )
        .get(
            pk=reservation_id
        )
    )

    if reservation.status != (
        BloodReservation.Status.ACTIVE
    ):
        raise ValidationError(
            "Only active reservations can be released."
        )

    inventory = reservation.inventory

    if inventory.status != (
        InventoryRecord.Status.RESERVED
    ):
        raise ValidationError(
            "Inventory is not currently reserved."
        )

    reservation.status = (
        BloodReservation.Status.CANCELLED
    )

    reservation.save(
        update_fields=["status"]
    )

    inventory.status = (
        InventoryRecord.Status.AVAILABLE
    )

    inventory.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    InventoryMovement.objects.create(
        inventory=inventory,
        movement_type=(
            InventoryMovement.MovementType.RELEASED
        ),
        to_location=inventory.storage_location,
        reason=(
            f"Reservation cancelled. "
            f"Reservation: {reservation.reservation_id}"
        ),
        created_by=released_by,
    )

    return inventory

@transaction.atomic
def issue_blood(
    inventory_id,
    facility,
    issued_by,
    patient_reference="",
    clinical_reference="",
    notes="",
):
    """
    Issue a blood unit from inventory.

    The unit must be available or reserved.
    """

    inventory = (
        InventoryRecord.objects
        .select_for_update()
        .select_related(
            "blood_unit",
            "storage_location",
        )
        .get(
            pk=inventory_id
        )
    )

    if inventory.facility_id != facility.id:
        raise ValidationError(
            "This blood unit does not belong to your facility."
        )

    if inventory.status not in [
        InventoryRecord.Status.AVAILABLE,
        InventoryRecord.Status.RESERVED,
    ]:
        raise ValidationError(
            "This blood unit cannot be issued in its current status."
        )

    unit = inventory.blood_unit

    if unit.expiry_date:
        if unit.expiry_date <= timezone.now():

            inventory.status = (
                InventoryRecord.Status.EXPIRED
            )

            inventory.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            raise ValidationError(
                "This blood unit has expired and cannot be issued."
            )

    issue = BloodIssue.objects.create(
        inventory=inventory,
        facility=facility,
        patient_reference=patient_reference,
        clinical_reference=clinical_reference,
        status=BloodIssue.IssueStatus.ISSUED,
        issued_by=issued_by,
        notes=notes,
    )

    inventory.status = (
        InventoryRecord.Status.ISSUED
    )

    inventory.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    unit.status = "DISPATCHED"

    unit.save(
        update_fields=["status"]
    )

    InventoryMovement.objects.create(
        inventory=inventory,
        movement_type=(
            InventoryMovement.MovementType.ISSUED
        ),
        from_location=inventory.storage_location,
        reason=(
            f"Blood unit issued. "
            f"Issue: {issue.issue_id}"
        ),
        created_by=issued_by,
    )

    return issue

@transaction.atomic
def return_blood(
    issue_id,
    returned_by,
    reason="",
):
    """
    Return an issued blood unit to available stock.
    """

    issue = (
        BloodIssue.objects
        .select_for_update()
        .select_related(
            "inventory",
            "inventory__blood_unit",
            "inventory__storage_location",
        )
        .get(
            pk=issue_id
        )
    )

    if issue.status != (
        BloodIssue.IssueStatus.ISSUED
    ):
        raise ValidationError(
            "Only issued blood units can be returned."
        )

    inventory = issue.inventory
    unit = inventory.blood_unit

    if unit.expiry_date:
        if unit.expiry_date <= timezone.now():

            inventory.status = (
                InventoryRecord.Status.EXPIRED
            )

            inventory.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            issue.status = (
                BloodIssue.IssueStatus.RETURNED
            )

            issue.save(
                update_fields=["status"]
            )

            raise ValidationError(
                "The returned blood unit has expired."
            )

    issue.status = (
        BloodIssue.IssueStatus.RETURNED
    )

    issue.save(
        update_fields=["status"]
    )

    inventory.status = (
        InventoryRecord.Status.AVAILABLE
    )

    inventory.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    unit.status = "RELEASED"

    unit.save(
        update_fields=["status"]
    )

    InventoryMovement.objects.create(
        inventory=inventory,
        movement_type=(
            InventoryMovement.MovementType.RETURNED
        ),
        to_location=inventory.storage_location,
        reason=reason or "Blood unit returned to inventory.",
        created_by=returned_by,
    )

    return inventory

@transaction.atomic
def mark_transfused(
    issue_id,
    recorded_by,
    notes="",
):
    """
    Mark an issued blood unit as transfused.
    """

    issue = (
        BloodIssue.objects
        .select_for_update()
        .select_related(
            "inventory",
            "inventory__blood_unit",
        )
        .get(
            pk=issue_id
        )
    )

    if issue.status != (
        BloodIssue.IssueStatus.ISSUED
    ):
        raise ValidationError(
            "Only issued blood can be marked as transfused."
        )

    issue.status = (
        BloodIssue.IssueStatus.TRANSFUSED
    )

    if notes:
        issue.notes = notes

    issue.save(
        update_fields=[
            "status",
            "notes",
        ]
    )

    inventory = issue.inventory

    inventory.status = (
        InventoryRecord.Status.TRANSFUSED
    )

    inventory.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    inventory.blood_unit.status = "TRANSFUSED"

    inventory.blood_unit.save(
        update_fields=["status"]
    )

    InventoryMovement.objects.create(
        inventory=inventory,
        movement_type=(
            InventoryMovement.MovementType.ISSUED
        ),
        reason=(
            f"Blood unit marked as transfused. "
            f"Issue: {issue.issue_id}"
        ),
        created_by=recorded_by,
    )

    return issue

@transaction.atomic
def discard_blood(
    inventory_id,
    discarded_by,
    reason,
):
    """
    Permanently mark a blood unit as discarded.
    """

    if not reason:
        raise ValidationError(
            "A reason is required when discarding blood."
        )

    inventory = (
        InventoryRecord.objects
        .select_for_update()
        .select_related(
            "blood_unit",
            "storage_location",
        )
        .get(
            pk=inventory_id
        )
    )

    allowed_statuses = [
        InventoryRecord.Status.QUARANTINED,
        InventoryRecord.Status.AVAILABLE,
        InventoryRecord.Status.RESERVED,
        InventoryRecord.Status.EXPIRED,
    ]

    if inventory.status not in allowed_statuses:
        raise ValidationError(
            "This blood unit cannot be discarded from its current status."
        )

    inventory.status = (
        InventoryRecord.Status.DISCARDED
    )

    inventory.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    inventory.blood_unit.status = "DISCARDED"

    inventory.blood_unit.save(
        update_fields=["status"]
    )

    InventoryMovement.objects.create(
        inventory=inventory,
        movement_type=(
            InventoryMovement.MovementType.DISCARDED
        ),
        from_location=inventory.storage_location,
        reason=reason,
        created_by=discarded_by,
    )

    return inventory

@transaction.atomic
def expire_blood_units():
    """
    Mark expired available/reserved blood units as expired.

    Returns the number of units expired.
    """

    now = timezone.now()

    inventories = (
        InventoryRecord.objects
        .select_for_update()
        .select_related("blood_unit")
        .filter(
            status__in=[
                InventoryRecord.Status.AVAILABLE,
                InventoryRecord.Status.RESERVED,
            ],
            blood_unit__expiry_date__isnull=False,
            blood_unit__expiry_date__lte=now,
        )
    )

    count = 0

    for inventory in inventories:

        inventory.status = (
            InventoryRecord.Status.EXPIRED
        )

        inventory.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        inventory.blood_unit.status = "EXPIRED"

        inventory.blood_unit.save(
            update_fields=["status"]
        )

        count += 1

    return count

@transaction.atomic
def request_transfer(
    inventory_id,
    destination_facility,
    requested_by,
    reason="",
    notes="",
):
    """
    Create a transfer request for an available blood unit.

    The inventory remains AVAILABLE until the transfer is dispatched.
    """

    inventory = (
        InventoryRecord.objects
        .select_for_update()
        .select_related(
            "blood_unit",
            "facility",
            "storage_location",
        )
        .get(pk=inventory_id)
    )

    if inventory.facility_id == destination_facility.pk:
        raise ValidationError(
            "Destination facility must be different from the source facility."
        )

    if inventory.status != InventoryRecord.Status.AVAILABLE:
        raise ValidationError(
            "Only available blood units can be requested for transfer."
        )

    if inventory.blood_unit.expiry_date <= timezone.localdate():
        raise ValidationError(
            "Expired blood cannot be transferred."
        )

    transfer = BloodTransfer.objects.create(
        blood_unit=inventory.blood_unit,
        from_facility=inventory.facility,
        to_facility=destination_facility,
        requested_by=requested_by,
        notes=(
            f"Reason: {reason}\n{notes}".strip()
            if reason
            else notes
        ),
        status=BloodTransfer.Status.REQUESTED,
    )

    InventoryMovement.objects.create(
        inventory=inventory,
        movement_type=InventoryMovement.MovementType.TRANSFERRED,
        from_location=inventory.storage_location,
        to_location=None,
        reason="Blood transfer requested.",
        created_by=requested_by,
    )

    return transfer


@transaction.atomic
def approve_transfer(
    transfer_id,
    approved_by,
):
    """
    Approve a requested transfer.

    Inventory remains AVAILABLE until dispatch.
    """

    transfer = (
        BloodTransfer.objects
        .select_for_update()
        .select_related(
            "blood_unit",
            "from_facility",
            "to_facility",
        )
        .get(pk=transfer_id)
    )

    if transfer.status != BloodTransfer.Status.REQUESTED:
        raise ValidationError(
            "Only requested transfers can be approved."
        )

    inventory = (
        InventoryRecord.objects
        .select_for_update()
        .select_related(
            "blood_unit",
            "facility",
            "storage_location",
        )
        .get(blood_unit=transfer.blood_unit)
    )

    if inventory.facility_id != transfer.from_facility_id:
        raise ValidationError(
            "Blood inventory is no longer held by the source facility."
        )

    if inventory.status != InventoryRecord.Status.AVAILABLE:
        raise ValidationError(
            "The blood unit is no longer available for transfer."
        )

    if inventory.blood_unit.expiry_date <= timezone.localdate():
        raise ValidationError(
            "Expired blood cannot be transferred."
        )

    transfer.status = BloodTransfer.Status.APPROVED
    transfer.save(update_fields=["status"])

    InventoryMovement.objects.create(
        inventory=inventory,
        movement_type=InventoryMovement.MovementType.TRANSFERRED,
        from_location=inventory.storage_location,
        to_location=None,
        reason="Blood transfer approved.",
        created_by=approved_by,
    )

    return transfer


@transaction.atomic
def dispatch_transfer(
    transfer_id,
    dispatched_by,
):
    """
    Dispatch an approved blood transfer.

    DISPATCHED represents the blood unit being in transit.
    """

    transfer = (
        BloodTransfer.objects
        .select_for_update()
        .select_related(
            "blood_unit",
            "from_facility",
            "to_facility",
        )
        .get(pk=transfer_id)
    )

    if transfer.status != BloodTransfer.Status.APPROVED:
        raise ValidationError(
            "Only approved transfers can be dispatched."
        )

    inventory = (
        InventoryRecord.objects
        .select_for_update()
        .select_related(
            "blood_unit",
            "facility",
            "storage_location",
        )
        .get(blood_unit=transfer.blood_unit)
    )

    if inventory.facility_id != transfer.from_facility_id:
        raise ValidationError(
            "Blood inventory is not currently held by the source facility."
        )

    if inventory.status != InventoryRecord.Status.AVAILABLE:
        raise ValidationError(
            "The blood unit is no longer available for dispatch."
        )

    if inventory.blood_unit.expiry_date <= timezone.localdate():
        raise ValidationError(
            "Expired blood cannot be dispatched."
        )

    source_location = inventory.storage_location

    inventory.status = InventoryRecord.Status.TRANSFERRED
    inventory.save(update_fields=["status", "updated_at"])

    transfer.status = BloodTransfer.Status.DISPATCHED
    transfer.dispatched_at = timezone.now()
    transfer.save(
        update_fields=[
            "status",
            "dispatched_at",
        ]
    )

    InventoryMovement.objects.create(
        inventory=inventory,
        movement_type=InventoryMovement.MovementType.TRANSFERRED,
        from_location=source_location,
        to_location=None,
        reason="Blood unit dispatched to destination facility.",
        created_by=dispatched_by,
    )

    return transfer


@transaction.atomic
def receive_transfer(
    transfer_id,
    received_by,
    storage_location=None,
):
    """
    Receive a dispatched blood unit at the destination facility.

    The inventory is moved to the destination facility and becomes AVAILABLE.
    """

    transfer = (
        BloodTransfer.objects
        .select_for_update()
        .select_related(
            "blood_unit",
            "from_facility",
            "to_facility",
        )
        .get(pk=transfer_id)
    )

    if transfer.status != BloodTransfer.Status.DISPATCHED:
        raise ValidationError(
            "Only dispatched transfers can be received."
        )

    inventory = (
        InventoryRecord.objects
        .select_for_update()
        .select_related(
            "blood_unit",
            "facility",
            "storage_location",
        )
        .get(blood_unit=transfer.blood_unit)
    )

    if inventory.status != InventoryRecord.Status.TRANSFERRED:
        raise ValidationError(
            "Inventory is not currently marked as transferred."
        )

    if inventory.facility_id != transfer.from_facility_id:
        raise ValidationError(
            "Inventory source facility does not match the transfer."
        )

    if inventory.blood_unit.expiry_date <= timezone.localdate():
        raise ValidationError(
            "This blood unit has expired and cannot be received as available stock."
        )

    if storage_location is None:
        raise ValidationError(
            "A destination storage location is required when receiving blood."
        )

    if storage_location.facility_id != transfer.to_facility_id:
        raise ValidationError(
            "Storage location must belong to the destination facility."
        )

    source_location = inventory.storage_location

    inventory.facility = transfer.to_facility
    inventory.storage_location = storage_location
    inventory.status = InventoryRecord.Status.AVAILABLE

    inventory.save(
        update_fields=[
            "facility",
            "storage_location",
            "status",
            "updated_at",
        ]
    )

    transfer.status = BloodTransfer.Status.RECEIVED
    transfer.received_at = timezone.now()

    transfer.save(
        update_fields=[
            "status",
            "received_at",
        ]
    )

    InventoryMovement.objects.create(
        inventory=inventory,
        movement_type=InventoryMovement.MovementType.MOVED,
        from_location=source_location,
        to_location=storage_location,
        reason="Blood unit received at destination facility.",
        created_by=received_by,
    )

    return transfer