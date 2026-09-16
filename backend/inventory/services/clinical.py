from django.db import transaction
from django.db.models import Q, Case, When, IntegerField
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from inventory.models import (
    InventoryRecord,
    BloodRequest,
    BloodReservation,
)

from inventory.models_clinical import (
    BloodRequestFulfillment,
    BloodRequestEvent,
)

from .compatibility import (
    is_blood_compatible,
)

from .transactions import (
    reserve_blood,
)


def find_compatible_inventory(
    facility,
    recipient_blood_group,
    component_type,
):
    """
    Find compatible available blood inventory.

    Selection follows FEFO:
    First Expiry, First Out.

    Blood units with an expiry date are prioritized before
    units without an expiry date.
    """

    inventories = (
        InventoryRecord.objects
        .select_related(
            "blood_unit",
            "storage_location",
            "facility",
        )
        .filter(
            facility=facility,
            status=InventoryRecord.Status.AVAILABLE,
            blood_unit__component_type__iexact=component_type,
        )
        .filter(
            Q(
                blood_unit__expiry_date__isnull=True
            )
            |
            Q(
                blood_unit__expiry_date__gt=timezone.now()
            )
        )
        .annotate(
            expiry_null=Case(
                When(
                    blood_unit__expiry_date__isnull=True,
                    then=1,
                ),
                default=0,
                output_field=IntegerField(),
            )
        )
        .order_by(
            "expiry_null",
            "blood_unit__expiry_date",
            "received_at",
            "id",
        )
    )

    compatible = []

    for inventory in inventories:

        if is_blood_compatible(
            inventory.blood_unit.blood_group,
            recipient_blood_group,
        ):
            compatible.append(inventory)

    return compatible


def get_request_fulfillment(
    blood_request,
):
    """
    Check how many compatible units are currently available
    for a blood request.

    This function does NOT reserve or change inventory.
    """

    compatible_inventory = find_compatible_inventory(
        facility=blood_request.facility,
        recipient_blood_group=blood_request.blood_group,
        component_type=blood_request.component_type,
    )

    available_units = len(compatible_inventory)

    requested_units = blood_request.requested_units

    if available_units >= requested_units:
        status = "FULFILLABLE"

    elif available_units > 0:
        status = "PARTIALLY_FULFILLABLE"

    else:
        status = "UNAVAILABLE"

    return {
        "request_id": blood_request.request_id,
        "requested_units": requested_units,
        "compatible_units": available_units,
        "status": status,
        "units": compatible_inventory,
    }


@transaction.atomic
def fulfill_blood_request(
    blood_request,
    created_by,
):
    """
    Reserve compatible blood units against a blood request.

    One BloodRequestFulfillment record is created for each
    inventory unit successfully reserved.

    The operation is atomic so that inventory changes and
    fulfillment records remain consistent.
    """

    request = (
        BloodRequest.objects
        .select_for_update()
        .select_related("facility")
        .get(pk=blood_request.pk)
    )

    if request.status in [
        BloodRequest.Status.CANCELLED,
        BloodRequest.Status.REJECTED,
        BloodRequest.Status.FULFILLED,
    ]:
        raise ValidationError(
            "This blood request cannot be fulfilled in its current status."
        )

    if request.requested_units <= 0:
        raise ValidationError(
            "Requested units must be greater than zero."
        )

    # Prevent duplicate active fulfillment of the same
    # inventory unit for the same request.
    existing_inventory_ids = set(
        BloodRequestFulfillment.objects
        .filter(
            blood_request=request,
            status__in=[
                BloodRequestFulfillment.Status.RESERVED,
                BloodRequestFulfillment.Status.ISSUED,
                BloodRequestFulfillment.Status.COMPLETED,
            ],
        )
        .values_list(
            "inventory_id",
            flat=True,
        )
    )

    compatible_inventory = find_compatible_inventory(
        facility=request.facility,
        recipient_blood_group=request.blood_group,
        component_type=request.component_type,
    )

    selected_inventory = [
        inventory
        for inventory in compatible_inventory
        if inventory.id not in existing_inventory_ids
    ]

    already_fulfilled = len(existing_inventory_ids)

    remaining_units = max(
        request.requested_units - already_fulfilled,
        0,
    )

    if remaining_units == 0:

        if request.status != BloodRequest.Status.FULFILLED:
            request.status = BloodRequest.Status.FULFILLED

            request.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        return list(
            BloodRequestFulfillment.objects.filter(
                blood_request=request,
            )
        )

    units_to_reserve = selected_inventory[:remaining_units]

    if not units_to_reserve:
        raise ValidationError(
            "No compatible available blood units are currently available."
        )

    created_fulfillments = []

    for inventory in units_to_reserve:

        reservation = reserve_blood(
            inventory_id=inventory.id,
            facility=request.facility,
            created_by=created_by,
            patient_reference=request.patient_reference,
            blood_group=request.blood_group,
            expires_at=request.required_by,
            notes=(
                f"Reserved for blood request "
                f"{request.request_id}."
            ),
        )

        fulfillment = BloodRequestFulfillment.objects.create(
            blood_request=request,
            inventory=inventory,
            status=BloodRequestFulfillment.Status.RESERVED,
            created_by=created_by,
            notes=(
                f"Reservation: "
                f"{reservation.reservation_id}"
            ),
        )

        created_fulfillments.append(
            fulfillment
        )

        BloodRequestEvent.objects.create(
            blood_request=request,
            event_type=(
                BloodRequestEvent.EventType.RESERVATION_CREATED
            ),
            performed_by=created_by,
            description=(
                f"Blood unit {inventory.blood_unit.unit_id} "
                f"reserved for request {request.request_id}."
            ),
            metadata={
                "inventory_id": inventory.inventory_id,
                "reservation_id": reservation.reservation_id,
                "unit_id": inventory.blood_unit.unit_id,
            },
        )

    total_fulfilled = (
        already_fulfilled
        + len(created_fulfillments)
    )

    if total_fulfilled >= request.requested_units:

        request.status = (
            BloodRequest.Status.FULFILLED
        )

        event_type = (
            BloodRequestEvent.EventType.FULFILLED
        )

        description = (
            f"Blood request {request.request_id} "
            f"fully fulfilled with "
            f"{total_fulfilled} unit(s)."
        )

    else:

        request.status = (
            BloodRequest.Status.PARTIALLY_FULFILLED
        )

        event_type = (
            BloodRequestEvent.EventType.PARTIALLY_FULFILLED
        )

        description = (
            f"Blood request {request.request_id} "
            f"partially fulfilled with "
            f"{total_fulfilled} of "
            f"{request.requested_units} unit(s)."
        )

    request.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    BloodRequestEvent.objects.create(
        blood_request=request,
        event_type=event_type,
        performed_by=created_by,
        description=description,
        metadata={
            "requested_units": request.requested_units,
            "fulfilled_units": total_fulfilled,
            "new_units_reserved": len(
                created_fulfillments
            ),
        },
    )

    return created_fulfillments