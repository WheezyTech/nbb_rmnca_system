from rest_framework.exceptions import ValidationError


ABO_COMPATIBILITY = {
    "O": ["O"],
    "A": ["A", "O"],
    "B": ["B", "O"],
    "AB": ["A", "B", "AB", "O"],
}


def normalize_blood_group(
    blood_group,
):
    if not blood_group:
        raise ValidationError(
            "Blood group is required."
        )

    value = blood_group.strip().upper()

    rh = ""

    if value.endswith("+"):
        abo = value[:-1]
        rh = "+"
    elif value.endswith("-"):
        abo = value[:-1]
        rh = "-"
    else:
        abo = value

    if abo not in ABO_COMPATIBILITY:
        raise ValidationError(
            f"Unsupported blood group: {blood_group}"
        )

    return abo, rh


def is_abo_compatible(
    donor_group,
    recipient_group,
):
    donor_abo, _ = normalize_blood_group(
        donor_group
    )

    recipient_abo, _ = normalize_blood_group(
        recipient_group
    )

    return (
        donor_abo
        in ABO_COMPATIBILITY[recipient_abo]
    )


def is_rh_compatible(
    donor_group,
    recipient_group,
):
    _, donor_rh = normalize_blood_group(
        donor_group
    )

    _, recipient_rh = normalize_blood_group(
        recipient_group
    )

    if not donor_rh or not recipient_rh:
        return True

    if recipient_rh == "+":
        return donor_rh in ["+", "-"]

    return donor_rh == "-"


def is_blood_compatible(
    donor_group,
    recipient_group,
):
    return (
        is_abo_compatible(
            donor_group,
            recipient_group,
        )
        and
        is_rh_compatible(
            donor_group,
            recipient_group,
        )
    )