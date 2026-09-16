from django.conf import settings
from django.core.mail import send_mail


def notify_transfer_users(
    transfer,
    subject,
    message,
):
    """
    Send transfer notification to relevant users.
    """

    users = []

    if transfer.requested_by:
        users.append(transfer.requested_by)

    if transfer.approved_by:
        users.append(transfer.approved_by)

    if transfer.dispatched_by:
        users.append(transfer.dispatched_by)

    if transfer.received_by:
        users.append(transfer.received_by)

    emails = list(
        {
            user.email
            for user in users
            if user.email
        }
    )

    if not emails:
        return 0

    return send_mail(
        subject=subject,
        message=message,
        from_email=getattr(
            settings,
            "DEFAULT_FROM_EMAIL",
            None,
        ),
        recipient_list=emails,
        fail_silently=True,
    )


def transfer_requested_notification(transfer):

    return notify_transfer_users(
        transfer,
        "Blood Transfer Requested",
        (
            f"Transfer {transfer.transfer_id} "
            "has been requested.\n\n"
            f"From: {transfer.from_facility.name}\n"
            f"To: {transfer.to_facility.name}\n"
            f"Blood group: "
            f"{transfer.blood_unit.blood_group}\n"
            f"Component: "
            f"{transfer.blood_unit.component_type}"
        ),
    )


def transfer_approved_notification(transfer):

    return notify_transfer_users(
        transfer,
        "Blood Transfer Approved",
        (
            f"Transfer {transfer.transfer_id} "
            "has been approved."
        ),
    )


def transfer_dispatched_notification(transfer):

    return notify_transfer_users(
        transfer,
        "Blood Transfer Dispatched",
        (
            f"Transfer {transfer.transfer_id} "
            "has been dispatched and is now in transit."
        ),
    )


def transfer_received_notification(transfer):

    return notify_transfer_users(
        transfer,
        "Blood Transfer Received",
        (
            f"Transfer {transfer.transfer_id} "
            "has been received at "
            f"{transfer.to_facility.name}."
        ),
    )
