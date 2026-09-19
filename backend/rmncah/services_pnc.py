from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models_pnc import (
    PNCVisit,
    NewbornCareRecord,
    PNCReferral,
    PNCFollowUp,
)


@transaction.atomic
def create_pnc_visit(
    pregnancy,
    delivery,
    attended_by,
    **kwargs,
):
    if pregnancy.facility_id != delivery.facility_id:
        raise ValidationError(
            "Pregnancy and delivery facility do not match."
        )

    return PNCVisit.objects.create(
        pregnancy=pregnancy,
        delivery=delivery,
        facility=pregnancy.facility,
        attended_by=attended_by,
        **kwargs,
    )


@transaction.atomic
def create_newborn_care_record(
    newborn,
    reviewed_by,
    **kwargs,
):
    return NewbornCareRecord.objects.create(
        newborn=newborn,
        pregnancy=newborn.pregnancy,
        delivery=newborn.delivery,
        facility=newborn.facility,
        reviewed_by=reviewed_by,
        **kwargs,
    )


@transaction.atomic
def create_pnc_referral(
    pregnancy,
    referred_by,
    to_facility,
    reason,
    newborn=None,
    **kwargs,
):
    if to_facility.id == pregnancy.facility_id:
        raise ValidationError(
            "Referral destination must be different "
            "from the current facility."
        )

    if newborn and newborn.pregnancy_id != pregnancy.id:
        raise ValidationError(
            "Newborn does not belong to this pregnancy."
        )

    return PNCReferral.objects.create(
        pregnancy=pregnancy,
        newborn=newborn,
        from_facility=pregnancy.facility,
        to_facility=to_facility,
        referred_by=referred_by,
        reason=reason,
        **kwargs,
    )


@transaction.atomic
def create_pnc_followup(
    pregnancy,
    created_by,
    newborn=None,
    **kwargs,
):
    if newborn and newborn.pregnancy_id != pregnancy.id:
        raise ValidationError(
            "Newborn does not belong to this pregnancy."
        )

    return PNCFollowUp.objects.create(
        pregnancy=pregnancy,
        newborn=newborn,
        facility=pregnancy.facility,
        created_by=created_by,
        **kwargs,
    )


@transaction.atomic
def complete_pnc_followup(
    followup,
    completed_by,
    notes="",
):
    if followup.status != PNCFollowUp.Status.SCHEDULED:
        raise ValidationError(
            "Only scheduled follow-ups can be completed."
        )

    followup.status = PNCFollowUp.Status.COMPLETED
    followup.completed_at = timezone.now()
    followup.completed_by = completed_by

    if notes:
        followup.notes = notes

    followup.save(
        update_fields=[
            "status",
            "completed_at",
            "completed_by",
            "notes",
            "updated_at",
        ]
    )

    return followup