def get_user_scope(user):
    """
    Returns the user's organizational scope.

    Possible values:
        national
        regional
        county
        facility
        none
    """

    if not user or not user.is_authenticated:
        return "none"

    if user.role in [
        "SUPER_ADMIN",
        "NATIONAL_ADMIN",
    ]:
        return "national"

    if user.role == "REGIONAL_ADMIN":
        return "regional"

    if user.role == "COUNTY_ADMIN":
        return "county"

    if user.role in [
        "FACILITY_ADMIN",
        "BLOOD_BANK_OFFICER",
        "LABORATORY_OFFICER",
        "INVENTORY_OFFICER",
        "CLINICIAN",
        "RMNCAH_OFFICER",
        "DATA_OFFICER",
        "AUDITOR",
    ]:
        return "facility"

    return "none"


def filter_by_facility_scope(
    queryset,
    user,
    facility_field="facility_id",
):
    """
    Restrict a queryset according to the user's
    organizational scope.
    """

    scope = get_user_scope(user)

    if scope == "national":
        return queryset

    if scope == "regional":

        if not user.facility_id:
            return queryset.none()

        region_id = user.facility.region_id

        return queryset.filter(
            **{
                f"{facility_field}__region_id": region_id
            }
        )

    if scope == "county":

        if not user.facility_id:
            return queryset.none()

        county_id = user.facility.county_id

        return queryset.filter(
            **{
                f"{facility_field}__county_id": county_id
            }
        )

    if scope == "facility":

        if not user.facility_id:
            return queryset.none()

        return queryset.filter(
            **{
                facility_field: user.facility_id
            }
        )

    return queryset.none()