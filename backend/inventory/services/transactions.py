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
                    "status": InventoryRecord.Status.AVAILABLE,
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
        InventoryRecord.Status.AVAILABLE
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

    If the unit is reserved for a blood request, the corresponding
    reservation and blood request fulfillment are updated as part
    of the same database transaction.
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

            unit.status = "EXPIRED"

            unit.save(
                update_fields=["status"]
            )

            raise ValidationError(
                "This blood unit has expired and cannot be issued."
            )

    # Handle active reservation if the unit is reserved
    reservation = None

    if inventory.status == (
        InventoryRecord.Status.RESERVED
    ):

        reservation = (
            BloodReservation.objects
            .select_for_update()
            .filter(
                inventory=inventory,
                facility=facility,
                status=BloodReservation.Status.ACTIVE,
            )
            .order_by("-reserved_at")
            .first()
        )

        if reservation is None:
            raise ValidationError(
                "This blood unit is marked as reserved, "
                "but no active reservation was found."
            )

        if (
            reservation.patient_reference
            and patient_reference
            and reservation.patient_reference
            != patient_reference
        ):
            raise ValidationError(
                "Patient reference does not match the active "
                "blood reservation."
            )

    issue = BloodIssue.objects.create(
        inventory=inventory,
        facility=facility,
        patient_reference=(
            patient_reference
            or (
                reservation.patient_reference
                if reservation
                else ""
            )
        ),
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

    if reservation:

        reservation.status = (
            BloodReservation.Status.FULFILLED
        )

        reservation.save(
            update_fields=["status"]
        )

    from inventory.models_clinical import (
        BloodRequestFulfillment,
        BloodRequestEvent,
    )

    fulfillment = (
        BloodRequestFulfillment.objects
        .select_for_update()
        .select_related(
            "blood_request",
        )
        .filter(
            inventory=inventory,
            status=BloodRequestFulfillment.Status.RESERVED,
        )
        .order_by("-created_at")
        .first()
    )

    if fulfillment:

        fulfillment.status = (
            BloodRequestFulfillment.Status.ISSUED
        )

        fulfillment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        BloodRequestEvent.objects.create(
            blood_request=fulfillment.blood_request,
            event_type=(
                BloodRequestEvent.EventType.BLOOD_ISSUED
            ),
            performed_by=issued_by,
            description=(
                f"Blood unit {unit.unit_id} "
                f"issued against request "
                f"{fulfillment.blood_request.request_id}."
            ),
            metadata={
                "inventory_id": inventory.inventory_id,
                "unit_id": unit.unit_id,
                "issue_id": issue.issue_id,
                "fulfillment_id": fulfillment.fulfillment_id,
                "reservation_id": (
                    reservation.reservation_id
                    if reservation
                    else None
                ),
            },
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

    If the issue originated from a blood request fulfillment,
    restore the related fulfillment and reservation so the
    clinical request remains traceable.
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

    # Check expiry before returning the unit to available stock.
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

            unit.status = "EXPIRED"

            unit.save(
                update_fields=["status"]
            )

            raise ValidationError(
                "The returned blood unit has expired."
            )

    # Update issue
    issue.status = (
        BloodIssue.IssueStatus.RETURNED
    )

    issue.save(
        update_fields=["status"]
    )

    # Return inventory to available stock
    inventory.status = (
        InventoryRecord.Status.AVAILABLE
    )

    inventory.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    # Return blood unit to released status
    unit.status = "RELEASED"

    unit.save(
        update_fields=["status"]
    )

    # Clinical blood-request reconciliation
    from inventory.models_clinical import (
        BloodRequestFulfillment,
        BloodRequestEvent,
    )

    fulfillment = (
        BloodRequestFulfillment.objects
        .select_for_update()
        .select_related(
            "blood_request",
        )
        .filter(
            inventory=inventory,
            status=BloodRequestFulfillment.Status.ISSUED,
        )
        .order_by("-created_at")
        .first()
    )

    reservation = None

    if fulfillment:

        reservation = (
            BloodReservation.objects
            .select_for_update()
            .filter(
                inventory=inventory,
                facility=issue.facility,
                status=BloodReservation.Status.FULFILLED,
            )
            .order_by("-reserved_at")
            .first()
        )

        # Restore fulfillment to RESERVED
        fulfillment.status = (
            BloodRequestFulfillment.Status.RESERVED
        )

        fulfillment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # Restore the reservation to ACTIVE
        if reservation:

            reservation.status = (
                BloodReservation.Status.ACTIVE
            )

            reservation.save(
                update_fields=["status"]
            )

        # Create clinical audit event
        BloodRequestEvent.objects.create(
            blood_request=fulfillment.blood_request,
            event_type=(
                BloodRequestEvent.EventType.BLOOD_RETURNED
            ),
            performed_by=returned_by,
            description=(
                f"Blood unit {unit.unit_id} returned "
                f"against request "
                f"{fulfillment.blood_request.request_id}."
            ),
            metadata={
                "inventory_id": inventory.inventory_id,
                "unit_id": unit.unit_id,
                "issue_id": issue.issue_id,
                "fulfillment_id": fulfillment.fulfillment_id,
                "reservation_id": (
                    reservation.reservation_id
                    if reservation
                    else None
                ),
                "reason": (
                    reason
                    or "Blood unit returned to inventory."
                ),
            },
        )

    # Inventory audit
    InventoryMovement.objects.create(
        inventory=inventory,
        movement_type=(
            InventoryMovement.MovementType.RETURNED
        ),
        to_location=inventory.storage_location,
        reason=(
            reason
            or "Blood unit returned to inventory."
        ),
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
        InventoryRecord.Status.AVAILABLE,
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

    if (
        inventory.blood_unit.expiry_date
        and inventory.blood_unit.expiry_date <= timezone.localdate()
    ):
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

    if (
        inventory.blood_unit.expiry_date
        and inventory.blood_unit.expiry_date <= timezone.localdate()
    ):
        raise ValidationError(
            "Expired blood cannot be transferred."
        )

    transfer.status = BloodTransfer.Status.APPROVED
    transfer.approved_by = approved_by
    transfer.approved_at = timezone.now()

    transfer.save(
        update_fields=[
            "status",
            "approved_by",
            "approved_at",
        ]
    )

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

    if (
        inventory.blood_unit.expiry_date
        and inventory.blood_unit.expiry_date <= timezone.localdate()
    ):
        raise ValidationError(
            "Expired blood cannot be dispatched."
        )

    source_location = inventory.storage_location

    inventory.status = InventoryRecord.Status.TRANSFERRED
    inventory.save(update_fields=["status", "updated_at"])

    transfer.status = BloodTransfer.Status.DISPATCHED
    transfer.dispatched_at = timezone.now()
    transfer.dispatched_by = dispatched_by
    transfer.save(
        update_fields=[
            "status",
            "dispatched_at",
            "dispatched_by",
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

    if received_by.facility_id != transfer.to_facility_id:
        raise ValidationError(
            "Only a user assigned to the destination facility "
            "can receive this transfer."
        )

    if storage_location is None:
        raise ValidationError(
            "A destination storage location is required."
        )

    if storage_location.facility_id != transfer.to_facility_id:
        raise ValidationError(
            "Storage location must belong to the destination facility."
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

    if (
        inventory.blood_unit.expiry_date
        and inventory.blood_unit.expiry_date <= timezone.now()
    ):
        inventory.status = InventoryRecord.Status.EXPIRED

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

        raise ValidationError(
            "This blood unit has expired and cannot be received."
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
    transfer.received_by = received_by

    transfer.save(
        update_fields=[
            "status",
            "received_at",
            "received_by",
        ]
    )

    transfer.blood_unit.facility = transfer.to_facility
    transfer.blood_unit.status = "RELEASED"

    transfer.blood_unit.save(
        update_fields=[
            "facility",
            "status",
        ]
    )

    InventoryMovement.objects.create(
        inventory=inventory,
        movement_type=InventoryMovement.MovementType.MOVED,
        from_location=source_location,
        to_location=storage_location,
        reason=(
            "Blood unit received at destination facility. "
            f"Transfer: {transfer.transfer_id}"
        ),
        created_by=received_by,
    )

    return transfer

@transaction.atomic
def reject_transfer(
    transfer_id,
    rejected_by,
    reason,
):
    """
    Reject/cancel a requested blood transfer.
    """

    if not reason:
        raise ValidationError(
            "A rejection reason is required."
        )

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
            "Only requested transfers can be rejected."
        )

    transfer.status = BloodTransfer.Status.CANCELLED
    transfer.rejected_by = rejected_by
    transfer.rejected_at = timezone.now()
    transfer.rejection_reason = reason

    transfer.save(
        update_fields=[
            "status",
            "rejected_by",
            "rejected_at",
            "rejection_reason",
        ]
    )

    inventory = (
        InventoryRecord.objects
        .filter(
            blood_unit=transfer.blood_unit,
        )
        .select_related(
            "storage_location",
        )
        .first()
    )

    if inventory:
        InventoryMovement.objects.create(
            inventory=inventory,
            movement_type=(
                InventoryMovement.MovementType.TRANSFERRED
            ),
            from_location=inventory.storage_location,
            to_location=None,
            reason=(
                f"Blood transfer rejected. "
                f"Transfer: {transfer.transfer_id}. "
                f"Reason: {reason}"
            ),
            created_by=rejected_by,
        )

    return transfer