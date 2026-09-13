from rest_framework.permissions import BasePermission


ROLE_LEVELS = {
    "SUPER_ADMIN": 100,
    "NATIONAL_ADMIN": 90,
    "REGIONAL_ADMIN": 80,
    "COUNTY_ADMIN": 70,
    "FACILITY_ADMIN": 60,
    "BLOOD_BANK_OFFICER": 50,
    "LABORATORY_OFFICER": 50,
    "INVENTORY_OFFICER": 50,
    "CLINICIAN": 40,
    "RMNCAH_OFFICER": 40,
    "DATA_OFFICER": 30,
    "AUDITOR": 20,
}


def is_authenticated(user):
    return (
        user is not None
        and user.is_authenticated
        and user.is_active
    )


def has_minimum_role(user, minimum_level):
    if not is_authenticated(user):
        return False

    return ROLE_LEVELS.get(user.role, 0) >= minimum_level


class IsSuperAdmin(BasePermission):

    def has_permission(self, request, view):
        return has_minimum_role(request.user, 100)


class IsNationalAdmin(BasePermission):

    def has_permission(self, request, view):
        return has_minimum_role(request.user, 90)


class IsRegionalAdmin(BasePermission):

    def has_permission(self, request, view):
        return has_minimum_role(request.user, 80)


class IsCountyAdmin(BasePermission):

    def has_permission(self, request, view):
        return has_minimum_role(request.user, 70)


class IsFacilityAdmin(BasePermission):

    def has_permission(self, request, view):
        return has_minimum_role(request.user, 60)


class IsBloodBankOfficer(BasePermission):

    def has_permission(self, request, view):
        if not is_authenticated(request.user):
            return False

        return request.user.role in [
            "SUPER_ADMIN",
            "NATIONAL_ADMIN",
            "REGIONAL_ADMIN",
            "COUNTY_ADMIN",
            "FACILITY_ADMIN",
            "BLOOD_BANK_OFFICER",
        ]


class IsLaboratoryOfficer(BasePermission):

    def has_permission(self, request, view):
        if not is_authenticated(request.user):
            return False

        return request.user.role in [
            "SUPER_ADMIN",
            "NATIONAL_ADMIN",
            "REGIONAL_ADMIN",
            "COUNTY_ADMIN",
            "FACILITY_ADMIN",
            "LABORATORY_OFFICER",
        ]


class IsRMNCAHOfficer(BasePermission):

    def has_permission(self, request, view):
        if not is_authenticated(request.user):
            return False

        return request.user.role in [
            "SUPER_ADMIN",
            "NATIONAL_ADMIN",
            "REGIONAL_ADMIN",
            "COUNTY_ADMIN",
            "FACILITY_ADMIN",
            "RMNCAH_OFFICER",
            "CLINICIAN",
        ]


class IsFacilityUser(BasePermission):

    def has_permission(self, request, view):
        return (
            is_authenticated(request.user)
            and request.user.facility_id is not None
        )