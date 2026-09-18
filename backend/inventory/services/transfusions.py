from django.core.exceptions import ValidationError
from django.db import transaction

from inventory.models import BloodIssue
from inventory.models_clinical import TransfusionEvent


@transaction.atomic
def record_transfusion(
    issue_id,
    recorded_by,
    transfused_at,
    patient_reference="",
    notes="",
):
    """
    Record a completed transfusion against an issued
    blood unit.

    One blood issue may only have one completed
    transfusion event.
    """

    issue = (
        BloodIssue.objects
        .select_for_update()
        .select_related(
            "inventory",
            "inventory__blood_unit",
            "facility",
        )
        .get(pk=issue_id)
    )

    if issue.status != BloodIssue.IssueStatus.TRANSFUSED:
        raise ValidationError(
            "Only blood marked as transfused can be "
            "recorded as a transfusion event."
        )

    if (
        recorded_by.facility_id
        and issue.facility_id != recorded_by.facility_id
    ):
        raise ValidationError(
            "You cannot record a transfusion outside "
            "your facility."
        )

    existing = (
        TransfusionEvent.objects
        .filter(
            blood_issue=issue,
            status=TransfusionEvent.Status.COMPLETED,
        )
        .exists()
    )

    if existing:
        raise ValidationError(
            "A completed transfusion event already "
            "exists for this blood issue."
        )

    patient_reference = (
        patient_reference
        or issue.patient_reference
    )

    if (
        issue.patient_reference
        and patient_reference
        != issue.patient_reference
    ):
        raise ValidationError(
            "Patient reference does not match "
            "the blood issue."
        )

    event = TransfusionEvent.objects.create(
        blood_issue=issue,
        facility=issue.facility,
        patient_reference=patient_reference,
        transfused_at=transfused_at,
        recorded_by=recorded_by,
        notes=notes,
        status=TransfusionEvent.Status.COMPLETED,
    )

    return event