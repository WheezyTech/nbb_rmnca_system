from django.core.exceptions import ValidationError
from django.db import transaction

from .models import PregnancyRecord
from .models_delivery import (
    DeliveryRecord,
    NewbornRecord,
    LabourRecord,
    PostnatalMotherRecord,
)


@transaction.atomic
def create_labour_record(
    pregnancy,
    managed_by,
    **kwargs,
):
    if pregnancy.status != PregnancyRecord.Status.ACTIVE:
        raise ValidationError(
            "Labour can only be started for an active pregnancy."
        )

    if hasattr(pregnancy, "labour"):
        raise ValidationError(
            "A labour record already exists for this pregnancy."
        )

    return LabourRecord.objects.create(
        pregnancy=pregnancy,
        facility=pregnancy.facility,
        managed_by=managed_by,
        **kwargs,
    )


@transaction.atomic
def record_delivery(
    pregnancy,
    attended_by,
    **kwargs,
):
    if pregnancy.status != PregnancyRecord.Status.ACTIVE:
        raise ValidationError(
            "Delivery can only be recorded for an active pregnancy."
        )

    if hasattr(pregnancy, "delivery"):
        raise ValidationError(
            "A delivery record already exists for this pregnancy."
        )

    delivery = DeliveryRecord.objects.create(
        pregnancy=pregnancy,
        facility=pregnancy.facility,
        attended_by=attended_by,
        **kwargs,
    )

    pregnancy.status = PregnancyRecord.Status.DELIVERED
    pregnancy.pregnancy_outcome = (
        delivery.delivery_mode
    )
    pregnancy.save(
        update_fields=[
            "status",
            "pregnancy_outcome",
            "updated_at",
        ]
    )

    LabourRecord.objects.filter(
        pregnancy=pregnancy,
        status__in=[
            LabourRecord.Status.ADMITTED,
            LabourRecord.Status.ACTIVE,
        ],
    ).update(
        status=LabourRecord.Status.DELIVERED
    )

    return delivery


@transaction.atomic
def record_newborn(
    delivery,
    recorded_by,
    **kwargs,
):
    if delivery.delivery_status == DeliveryRecord.DeliveryStatus.REFERRED:
        raise ValidationError(
            "Newborn cannot be recorded against a referred delivery."
        )

    return NewbornRecord.objects.create(
        delivery=delivery,
        pregnancy=delivery.pregnancy,
        facility=delivery.facility,
        recorded_by=recorded_by,
        **kwargs,
    )


@transaction.atomic
def create_postnatal_assessment(
    delivery,
    reviewed_by,
    **kwargs,
):
    return PostnatalMotherRecord.objects.create(
        pregnancy=delivery.pregnancy,
        delivery=delivery,
        facility=delivery.facility,
        reviewed_by=reviewed_by,
        **kwargs,
    )