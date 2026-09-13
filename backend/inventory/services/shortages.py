from django.db.models import Count

from inventory.models import InventoryRecord
from facilities.models import Facility


def get_zero_stock_by_facility():
    """
    Detect facilities that have zero AVAILABLE
    blood stock by blood group and component.
    """

    facilities = Facility.objects.all().order_by("name")

    results = []

    # Get all blood group/component combinations
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

    for facility in facilities:

        available = (
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

        available_map = {
            (
                item["blood_unit__blood_group"],
                item["blood_unit__component_type"],
            ): item["units"]
            for item in available
        }

        zero_stock = []

        for blood_group, component_type in combinations:

            units = available_map.get(
                (blood_group, component_type),
                0,
            )

            if units == 0:
                zero_stock.append(
                    {
                        "blood_group": blood_group,
                        "component_type": component_type,
                        "available_units": 0,
                    }
                )

        results.append(
            {
                "facility_id": facility.id,
                "facility_name": facility.name,
                "zero_stock": zero_stock,
                "zero_stock_count": len(zero_stock),
            }
        )

    return results


def get_facility_shortage_ranking():
    """
    Rank facilities according to their available
    blood-stock shortage.

    Facilities with zero available stock are ranked
    first.
    """

    facilities = Facility.objects.all()

    ranking = []

    for facility in facilities:

        total_units = (
            InventoryRecord.objects
            .filter(facility=facility)
            .count()
        )

        available_units = (
            InventoryRecord.objects
            .filter(
                facility=facility,
                status=InventoryRecord.Status.AVAILABLE,
            )
            .count()
        )

        unavailable_units = (
            total_units - available_units
        )

        zero_stock = available_units == 0

        ranking.append(
            {
                "facility_id": facility.id,
                "facility_name": facility.name,
                "total_units": total_units,
                "available_units": available_units,
                "unavailable_units": unavailable_units,
                "zero_stock": zero_stock,
            }
        )

    ranking.sort(
        key=lambda item: (
            item["zero_stock"],
            item["unavailable_units"],
        ),
        reverse=True,
    )

    for position, item in enumerate(
        ranking,
        start=1,
    ):
        item["rank"] = position

    return ranking