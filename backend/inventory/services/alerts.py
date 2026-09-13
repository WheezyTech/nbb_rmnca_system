from django.db.models import Count

from inventory.models import (
    InventoryRecord,
    BloodStockAlert,
)

from facilities.models import Facility


# Default thresholds
LOW_STOCK_THRESHOLD = 5
CRITICAL_STOCK_THRESHOLD = 2


def get_stock_alert(units):
    """
    Determine the alert level based on
    the number of AVAILABLE blood units.
    """

    if units == 0:
        return "ZERO_STOCK"

    if units <= CRITICAL_STOCK_THRESHOLD:
        return "CRITICAL"

    if units <= LOW_STOCK_THRESHOLD:
        return "LOW"

    return "NORMAL"


def generate_shortage_alerts():
    """
    Detect shortages for every facility and
    blood group/component combination.

    This function returns the current shortage
    information without creating database records.
    """

    facilities = Facility.objects.all().order_by("name")

    combinations = (
        InventoryRecord.objects
        .values(
            "blood_unit__blood_group",
            "blood_unit__component_type",
        )
        .distinct()
    )

    combinations = [
        (
            item["blood_unit__blood_group"],
            item["blood_unit__component_type"],
        )
        for item in combinations
    ]

    alerts = []

    for facility in facilities:

        available_stock = (
            InventoryRecord.objects
            .filter(
                facility=facility,
                status=InventoryRecord.Status.AVAILABLE,
            )
            .values(
                "blood_unit__blood_group",
                "blood_unit__component_type",
            )
            .annotate(
                units=Count("id")
            )
        )

        stock_map = {
            (
                item["blood_unit__blood_group"],
                item["blood_unit__component_type"],
            ): item["units"]
            for item in available_stock
        }

        for blood_group, component_type in combinations:

            units = stock_map.get(
                (blood_group, component_type),
                0,
            )

            alert_level = get_stock_alert(units)

            if alert_level == "NORMAL":
                continue

            alerts.append(
                {
                    "facility_id": facility.id,
                    "facility_name": facility.name,
                    "blood_group": blood_group,
                    "component_type": component_type,
                    "available_units": units,
                    "alert_level": alert_level,
                }
            )

    return alerts


def get_stock_alerts():
    """
    Backward-compatible helper used by the API.
    """

    return generate_shortage_alerts()


def persist_shortage_alerts():
    """
    Detect current shortages and persist them
    as database alerts.

    Existing OPEN or ACKNOWLEDGED alerts are updated
    rather than duplicated.

    Resolved alerts are reopened if the same shortage
    occurs again.
    """

    shortages = generate_shortage_alerts()

    persisted_alerts = []

    for shortage in shortages:

        facility_id = shortage["facility_id"]
        blood_group = shortage["blood_group"]
        component_type = shortage["component_type"]
        available_units = shortage["available_units"]
        alert_level = shortage["alert_level"]

        alert = (
            BloodStockAlert.objects
            .filter(
                facility_id=facility_id,
                blood_group=blood_group,
                component_type=component_type,
            )
            .order_by("-created_at")
            .first()
        )

        if alert is None:

            alert = BloodStockAlert.objects.create(
                facility_id=facility_id,
                blood_group=blood_group,
                component_type=component_type,
                available_units=available_units,
                alert_level=alert_level,
                status=BloodStockAlert.AlertStatus.OPEN,
            )

        else:

            alert.available_units = available_units
            alert.alert_level = alert_level

            if (
                alert.status
                == BloodStockAlert.AlertStatus.RESOLVED
            ):
                alert.status = (
                    BloodStockAlert.AlertStatus.OPEN
                )

                alert.acknowledged_at = None
                alert.acknowledged_by = None
                alert.resolved_at = None
                alert.resolved_by = None
                alert.resolution_notes = ""

            alert.save()

        persisted_alerts.append(alert)

    return persisted_alerts