from django.db import transaction
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from inventory.models import BloodIssue
from inventory.models_clinical import TransfusionReaction


@transaction.atomic
def report_transfusion_reaction(
    blood_issue,
    reported_by,
    reaction_type,
    severity,
    reaction_date,
    symptoms="",
    clinical_action="",
    notes="",
):
    """
    Report a suspected transfusion reaction against
    an actual blood transfusion.

    A reaction can only be reported against a blood issue
    whose status is TRANSFUSED.
    """

    # Lock the issue during the operation.
    issue = (
        BloodIssue.objects
        .select_for_update()
        .select_related(
            "inventory",
            "inventory__blood_unit",
            "facility",
        )
        .get(pk=blood_issue.pk)
    )

    # --------------------------------------------------
    # 1. Validate issue status
    # --------------------------------------------------

    if issue.status != BloodIssue.IssueStatus.TRANSFUSED:
        raise ValidationError(
            "A transfusion reaction can only be reported "
            "against a blood unit that has been marked as transfused."
        )

    # --------------------------------------------------
    # 2. Validate reporting user
    # --------------------------------------------------

    if reported_by is None:
        raise ValidationError(
            "A user is required to report a transfusion reaction."
        )

    if not reported_by.is_active:
        raise ValidationError(
            "The reporting user is not active."
        )

    # --------------------------------------------------
    # 3. Validate facility
    # --------------------------------------------------

    if (
        reported_by.facility_id
        and reported_by.facility_id != issue.facility_id
    ):
        raise ValidationError(
            "The reporting user does not belong to "
            "the facility where the transfusion occurred."
        )

    # --------------------------------------------------
    # 4. Validate reaction type
    # --------------------------------------------------

    valid_reaction_types = {
        choice[0]
        for choice in TransfusionReaction.ReactionType.choices
    }

    if reaction_type not in valid_reaction_types:
        raise ValidationError(
            "Invalid transfusion reaction type."
        )

    # --------------------------------------------------
    # 5. Validate severity
    # --------------------------------------------------

    valid_severities = {
        choice[0]
        for choice in TransfusionReaction.Severity.choices
    }

    if severity not in valid_severities:
        raise ValidationError(
            "Invalid transfusion reaction severity."
        )

    # --------------------------------------------------
    # 6. Validate reaction date
    # --------------------------------------------------

    if reaction_date is None:
        raise ValidationError(
            "Reaction date and time are required."
        )

    if timezone.is_naive(reaction_date):
        raise ValidationError(
            "Reaction date and time must be timezone-aware."
        )

    if reaction_date > timezone.now():
        raise ValidationError(
            "Reaction date and time cannot be in the future."
        )

    # --------------------------------------------------
    # 7. Prevent duplicate reaction records
    # --------------------------------------------------

    existing_reaction = (
        TransfusionReaction.objects
        .filter(
            blood_issue=issue,
            status__in=[
                TransfusionReaction.Status.REPORTED,
                TransfusionReaction.Status.UNDER_INVESTIGATION,
                TransfusionReaction.Status.CONFIRMED,
            ],
        )
        .first()
    )

    if existing_reaction:
        raise ValidationError(
            "An active transfusion reaction has already "
            "been reported for this blood issue."
        )

    # --------------------------------------------------
    # 8. Create reaction record
    # --------------------------------------------------

    reaction = TransfusionReaction.objects.create(
        blood_issue=issue,
        facility=issue.facility,
        patient_reference=issue.patient_reference,
        reaction_type=reaction_type,
        severity=severity,
        status=TransfusionReaction.Status.REPORTED,
        symptoms=symptoms,
        reaction_date=reaction_date,
        reported_by=reported_by,
        clinical_action=clinical_action,
        notes=notes,
    )

    return reaction