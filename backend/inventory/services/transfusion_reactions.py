from django.core.exceptions import ValidationError
from django.db import transaction

from inventory.models_clinical import (
    TransfusionReaction,
    TransfusionReactionEvent,
)


ALLOWED_TRANSITIONS = {
    TransfusionReaction.Status.REPORTED: {
        TransfusionReaction.Status.UNDER_INVESTIGATION,
    },

    TransfusionReaction.Status.UNDER_INVESTIGATION: {
        TransfusionReaction.Status.CONFIRMED,
        TransfusionReaction.Status.RULED_OUT,
    },

    TransfusionReaction.Status.CONFIRMED: {
        TransfusionReaction.Status.CLOSED,
    },

    TransfusionReaction.Status.RULED_OUT: {
        TransfusionReaction.Status.CLOSED,
    },

    TransfusionReaction.Status.CLOSED: set(),
}


EVENT_TYPES = {
    TransfusionReaction.Status.REPORTED:
        TransfusionReactionEvent.EventType.REPORTED,

    TransfusionReaction.Status.UNDER_INVESTIGATION:
        TransfusionReactionEvent.EventType.INVESTIGATION_STARTED,

    TransfusionReaction.Status.CONFIRMED:
        TransfusionReactionEvent.EventType.CONFIRMED,

    TransfusionReaction.Status.RULED_OUT:
        TransfusionReactionEvent.EventType.RULED_OUT,

    TransfusionReaction.Status.CLOSED:
        TransfusionReactionEvent.EventType.CLOSED,
}


@transaction.atomic
def transition_reaction(
    reaction_id,
    new_status,
    performed_by,
    notes="",
):
    reaction = (
        TransfusionReaction.objects
        .select_for_update()
        .get(pk=reaction_id)
    )

    current_status = reaction.status

    allowed_statuses = ALLOWED_TRANSITIONS.get(
        current_status,
        set(),
    )

    if new_status not in allowed_statuses:
        raise ValidationError(
            f"Invalid transfusion reaction status transition: "
            f"{current_status} -> {new_status}."
        )

    if (
        performed_by.facility_id
        and reaction.facility_id
        != performed_by.facility_id
    ):
        raise ValidationError(
            "You cannot modify a transfusion reaction "
            "outside your facility."
        )

    reaction.status = new_status

    if notes:
        reaction.notes = notes

    reaction.save(
        update_fields=[
            "status",
            "notes",
            "updated_at",
        ]
    )

    TransfusionReactionEvent.objects.create(
        reaction=reaction,
        event_type=EVENT_TYPES[new_status],
        performed_by=performed_by,
        previous_status=current_status,
        new_status=new_status,
        description=(
            f"Transfusion reaction "
            f"{reaction.reaction_id} changed from "
            f"{current_status} to {new_status}."
        ),
        metadata={
            "reaction_id": reaction.reaction_id,
            "previous_status": current_status,
            "new_status": new_status,
            "notes": notes,
        },
    )

    return reaction