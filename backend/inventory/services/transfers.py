from django.db import transaction
from django.db.models import Count

from rest_framework.exceptions import ValidationError

from inventory.models import (
    InventoryRecord,
    BloodStockAlert,
    BloodTransfer,
)
from facilities.models import Facility


# ---------------------------------------------------------
# TRANSFER RECOMMENDATION SETTINGS
# ---------------------------------------------------------

# Source facility must retain at least this many units
# before recommending a transfer.
MIN_SOURCE_RESERVE = 5


# Maximum number of recommendations returned by default.
DEFAULT_LIMIT = 50


def get_transfer_recommendations(limit=DEFAULT_LIMIT):
    """
    Generate ranked blood transfer recommendations.

    The function does NOT create or approve transfers.

    It identifies:
        - facilities with blood shortages
        - facilities with transferable surplus
        - matching blood group/component combinations

    Recommendations are ranked by shortage severity.
    """

    facilities = Facility.objects.all().order_by("name")

    recommendations = []

    # -----------------------------------------------------
    # STEP 1 — BUILD STOCK MAP
    # -----------------------------------------------------

    stock_rows = (
        InventoryRecord.objects
        .filter(
            status=InventoryRecord.Status.AVAILABLE
        )
        .values(
            "facility_id",
            "facility__name",
            "blood_unit__blood_group",
            "blood_unit__component_type",
        )
        .annotate(
            units=Count("id")
        )
    )

    stock_map = {}

    for row in stock_rows:

        key = (
            row["facility_id"],
            row["blood_unit__blood_group"],
            row["blood_unit__component_type"],
        )

        stock_map[key] = row["units"]

    # -----------------------------------------------------
    # STEP 2 — BUILD FACILITY SHORTAGE MAP
    # -----------------------------------------------------

    alert_rows = (
        BloodStockAlert.objects
        .filter(
            status__in=[
                BloodStockAlert.AlertStatus.OPEN,
                BloodStockAlert.AlertStatus.ACKNOWLEDGED,
            ]
        )
        .values(
            "facility_id",
            "blood_group",
            "component_type",
            "available_units",
            "alert_level",
        )
    )

    shortage_map = {}

    for alert in alert_rows:

        key = (
            alert["facility_id"],
            alert["blood_group"],
            alert["component_type"],
        )

        shortage_map[key] = alert

    # -----------------------------------------------------
    # STEP 3 — DETERMINE ALL BLOOD COMBINATIONS
    # -----------------------------------------------------

    combinations = set()

    for row in stock_rows:

        combinations.add(
            (
                row["blood_unit__blood_group"],
                row["blood_unit__component_type"],
            )
        )

    for alert in alert_rows:

        combinations.add(
            (
                alert["blood_group"],
                alert["component_type"],
            )
        )

    # -----------------------------------------------------
    # STEP 4 — FIND SHORTAGE FACILITIES
    # -----------------------------------------------------

    shortage_priority = {
        BloodStockAlert.AlertLevel.ZERO_STOCK: 3,
        BloodStockAlert.AlertLevel.CRITICAL: 2,
        BloodStockAlert.AlertLevel.LOW: 1,
    }

    shortage_facilities = []

    for facility in facilities:

        for blood_group, component_type in combinations:

            key = (
                facility.id,
                blood_group,
                component_type,
            )

            alert = shortage_map.get(key)

            if alert is None:
                continue

            alert_level = alert["alert_level"]

            if alert_level not in shortage_priority:
                continue

            shortage_facilities.append(
                {
                    "facility": facility,
                    "blood_group": blood_group,
                    "component_type": component_type,
                    "available_units": alert[
                        "available_units"
                    ],
                    "alert_level": alert_level,
                    "priority": shortage_priority[
                        alert_level
                    ],
                }
            )

    # -----------------------------------------------------
    # STEP 5 — FIND SURPLUS FACILITIES
    # -----------------------------------------------------

    surplus_facilities = []

    for facility in facilities:

        for blood_group, component_type in combinations:

            key = (
                facility.id,
                blood_group,
                component_type,
            )

            available_units = stock_map.get(
                key,
                0,
            )

            transferable_units = (
                available_units
                - MIN_SOURCE_RESERVE
            )

            if transferable_units <= 0:
                continue

            surplus_facilities.append(
                {
                    "facility": facility,
                    "blood_group": blood_group,
                    "component_type": component_type,
                    "available_units": available_units,
                    "transferable_units": transferable_units,
                }
            )

    # -----------------------------------------------------
    # STEP 6 — MATCH SURPLUS TO SHORTAGE
    # -----------------------------------------------------

    for shortage in shortage_facilities:

        shortage_facility = shortage["facility"]

        blood_group = shortage["blood_group"]
        component_type = shortage["component_type"]

        shortage_units = shortage[
            "available_units"
        ]

        # Desired stock level.
        #
        # LOW / CRITICAL facilities should receive enough
        # to move them above the shortage threshold.
        target_units = 6

        units_needed = max(
            target_units - shortage_units,
            1,
        )

        for surplus in surplus_facilities:

            source_facility = surplus["facility"]

            # Never transfer within the same facility.
            if (
                source_facility.id
                == shortage_facility.id
            ):
                continue

            # Blood group must match.
            if (
                surplus["blood_group"]
                != blood_group
            ):
                continue

            # Component must match.
            if (
                surplus["component_type"]
                != component_type
            ):
                continue

            transferable = min(
                units_needed,
                surplus["transferable_units"],
            )

            if transferable <= 0:
                continue

            recommendations.append(
                {
                    "source_facility_id": (
                        source_facility.id
                    ),

                    "source_facility": (
                        source_facility.name
                    ),

                    "destination_facility_id": (
                        shortage_facility.id
                    ),

                    "destination_facility": (
                        shortage_facility.name
                    ),

                    "blood_group": blood_group,

                    "component_type": (
                        component_type
                    ),

                    "source_available_units": (
                        surplus["available_units"]
                    ),

                    "source_transferable_units": (
                        surplus[
                            "transferable_units"
                        ]
                    ),

                    "destination_available_units": (
                        shortage_units
                    ),

                    "recommended_units": (
                        transferable
                    ),

                    "shortage_level": (
                        shortage["alert_level"]
                    ),

                    "priority": (
                        shortage["priority"]
                    ),
                }
            )

            # We have satisfied this shortage.
            units_needed -= transferable

            if units_needed <= 0:
                break

    # -----------------------------------------------------
    # STEP 7 — RANK RECOMMENDATIONS
    # -----------------------------------------------------

    recommendations.sort(
        key=lambda item: (
            item["priority"],
            -item["destination_available_units"],
            -item["recommended_units"],
        ),
        reverse=True,
    )

    return recommendations[:limit]


def get_transfer_opportunity(
    source_facility_id,
    destination_facility_id,
    blood_group,
    component_type,
):
    """
    Return one detailed transfer opportunity.

    This is a calculated recommendation only.
    It does NOT create a BloodTransfer.
    """

    recommendations = get_transfer_recommendations(
        limit=DEFAULT_LIMIT
    )

    for recommendation in recommendations:

        if (
            recommendation["source_facility_id"]
            != source_facility_id
        ):
            continue

        if (
            recommendation["destination_facility_id"]
            != destination_facility_id
        ):
            continue

        if (
            recommendation["blood_group"]
            != blood_group
        ):
            continue

        if (
            recommendation["component_type"]
            != component_type
        ):
            continue

        return recommendation

    return None


@transaction.atomic
def request_transfer_from_recommendation(
    source_facility_id,
    destination_facility_id,
    blood_group,
    component_type,
    requested_units,
    requested_by,
    reason="",
    notes="",
):
    """
    Convert a transfer recommendation into actual
    BloodTransfer request records.

    The recommendation itself is NOT a transfer.

    This function:
        1. validates the recommendation
        2. finds matching available blood
        3. creates transfer requests
        4. leaves inventory AVAILABLE

    Actual inventory movement happens later during
    transfer dispatch.
    """

    if requested_units <= 0:
        raise ValidationError(
            "Requested units must be greater than zero."
        )

    # -------------------------------------------------
    # VERIFY RECOMMENDATION
    # -------------------------------------------------

    opportunity = get_transfer_opportunity(
        source_facility_id=source_facility_id,
        destination_facility_id=destination_facility_id,
        blood_group=blood_group,
        component_type=component_type,
    )

    if opportunity is None:
        raise ValidationError(
            "No active transfer recommendation exists "
            "for the supplied facilities and blood type."
        )

    recommended_units = opportunity[
        "recommended_units"
    ]

    transferable_units = opportunity[
        "source_transferable_units"
    ]

    if requested_units > recommended_units:
        raise ValidationError(
            (
                "Requested quantity exceeds the "
                f"recommended quantity of "
                f"{recommended_units} units."
            )
        )

    if requested_units > transferable_units:
        raise ValidationError(
            (
                "Requested quantity exceeds the "
                f"transferable surplus of "
                f"{transferable_units} units."
            )
        )

    # -------------------------------------------------
    # FIND MATCHING AVAILABLE BLOOD
    # -------------------------------------------------

    inventories = (
        InventoryRecord.objects
        .select_for_update()
        .select_related(
            "blood_unit",
            "facility",
            "storage_location",
        )
        .filter(
            facility_id=source_facility_id,
            status=InventoryRecord.Status.AVAILABLE,
            blood_unit__blood_group=blood_group,
            blood_unit__component_type=component_type,
        )
        .order_by(
            "blood_unit__expiry_date",
            "received_at",
        )
    )

    available_count = inventories.count()

    if available_count < requested_units:
        raise ValidationError(
            (
                "There are not enough available matching "
                f"blood units. Requested: "
                f"{requested_units}, available: "
                f"{available_count}."
            )
        )

    # -------------------------------------------------
    # CREATE TRANSFER REQUESTS
    # -------------------------------------------------

    selected_inventories = list(
        inventories[:requested_units]
    )

    transfers = []

    for inventory in selected_inventories:

        transfer = BloodTransfer.objects.create(
            blood_unit=inventory.blood_unit,
            from_facility=inventory.facility,
            to_facility_id=destination_facility_id,
            requested_by=requested_by,
            notes=(
                f"Reason: {reason}\n{notes}".strip()
                if reason
                else notes
            ),
            status=BloodTransfer.Status.REQUESTED,
        )

        transfers.append(transfer)

    return transfers