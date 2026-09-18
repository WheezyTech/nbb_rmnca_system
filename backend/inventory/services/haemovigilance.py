from django.core.exceptions import PermissionDenied
from django.db.models import Count

NATIONAL_ROLES = {
    "SUPER_ADMIN",
    "NATIONAL_ADMIN",
}

REGIONAL_ROLES = {
    "REGIONAL_ADMIN",
}

COUNTY_ROLES = {
    "COUNTY_ADMIN",
}


def get_haemovigilance_scope(user):
    """
    Determine the geographical scope available to a user.
    """

    if not user.is_authenticated:
        raise PermissionDenied(
            "Authentication is required."
        )

    role = getattr(user, "role", None)

    # ---------------------------------------------------------
    # NATIONAL
    # ---------------------------------------------------------
    if role in NATIONAL_ROLES:
        return {
            "level": "NATIONAL",
            "facility_ids": None,
            "county_ids": None,
            "region_ids": None,
        }

    # ---------------------------------------------------------
    # REGIONAL
    # ---------------------------------------------------------
    if role in REGIONAL_ROLES:

        if not user.facility_id:
            raise PermissionDenied(
                "Regional administrator is not assigned "
                "to a facility."
            )

        if not user.facility.county_id:
            raise PermissionDenied(
                "User facility is not assigned to a county."
            )

        if not user.facility.county.region_id:
            raise PermissionDenied(
                "User facility county is not assigned "
                "to a region."
            )

        return {
            "level": "REGIONAL",
            "facility_ids": None,
            "county_ids": None,
            "region_ids": {
                user.facility.county.region_id
            },
        }

    # ---------------------------------------------------------
    # COUNTY
    # ---------------------------------------------------------
    if role in COUNTY_ROLES:

        if not user.facility_id:
            raise PermissionDenied(
                "County administrator is not assigned "
                "to a facility."
            )

        if not user.facility.county_id:
            raise PermissionDenied(
                "User facility is not assigned to a county."
            )

        return {
            "level": "COUNTY",
            "facility_ids": None,
            "county_ids": {
                user.facility.county_id
            },
            "region_ids": None,
        }

    # ---------------------------------------------------------
    # FACILITY
    # ---------------------------------------------------------
    if not user.facility_id:
        raise PermissionDenied(
            "Your account is not assigned to a facility."
        )

    return {
        "level": "FACILITY",
        "facility_ids": {
            user.facility_id
        },
        "county_ids": None,
        "region_ids": None,
    }


def apply_haemovigilance_scope(queryset, user):
    """
    Apply the user's geographical reporting scope
    to a HaemovigilanceReport queryset.
    """

    scope = get_haemovigilance_scope(user)

    if scope["level"] == "NATIONAL":
        return queryset

    if scope["level"] == "REGIONAL":
        return queryset.filter(
            facility__county__region_id__in=(
                scope["region_ids"]
            )
        )

    if scope["level"] == "COUNTY":
        return queryset.filter(
            facility__county_id__in=(
                scope["county_ids"]
            )
        )

    return queryset.filter(
        facility_id__in=scope["facility_ids"]
    )

def build_haemovigilance_aggregation(
    reports,
    level="NATIONAL",
):
    """
    Build aggregate haemovigilance statistics.

    The supplied queryset must already be geographically scoped.
    """

    from inventory.models_clinical import (
        HaemovigilanceReport,
        TransfusionReaction,
    )

    reactions = TransfusionReaction.objects.filter(
        haemovigilance_report__in=reports
    )

    # ---------------------------------------------------------
    # REPORT STATUS
    # ---------------------------------------------------------

    report_status = {
        status: reports.filter(
            status=status
        ).count()
        for status, _ in (
            HaemovigilanceReport.Status.choices
        )
    }

    # ---------------------------------------------------------
    # REACTION STATUS
    # ---------------------------------------------------------

    reaction_status = {
        status: reactions.filter(
            status=status
        ).count()
        for status, _ in (
            TransfusionReaction.Status.choices
        )
    }

    # ---------------------------------------------------------
    # SEVERITY
    # ---------------------------------------------------------

    severity = {
        value: reactions.filter(
            severity=value
        ).count()
        for value, _ in (
            TransfusionReaction.Severity.choices
        )
    }

    # ---------------------------------------------------------
    # REACTION TYPE
    # ---------------------------------------------------------

    reaction_types = {
        value: reactions.filter(
            reaction_type=value
        ).count()
        for value, _ in (
            TransfusionReaction.ReactionType.choices
        )
    }

    # ---------------------------------------------------------
    # OUTCOME
    # ---------------------------------------------------------

    outcomes = {
        value: reports.filter(
            outcome=value
        ).count()
        for value, _ in (
            HaemovigilanceReport.Outcome.choices
        )
    }

    # ---------------------------------------------------------
    # REPORT TYPE
    # ---------------------------------------------------------

    report_types = {
        value: reports.filter(
            report_type=value
        ).count()
        for value, _ in (
            HaemovigilanceReport.ReportType.choices
        )
    }

    # ---------------------------------------------------------
    # IMPUTABILITY
    # ---------------------------------------------------------

    imputability = {
        value: reports.filter(
            imputability=value
        ).count()
        for value, _ in (
            HaemovigilanceReport.Imputability.choices
        )
    }

    return {
        "aggregation_level": level,

        "reports": {
            "total": reports.count(),
            "status": report_status,
            "report_types": report_types,
            "imputability": imputability,
        },

        "reactions": {
            "total": reactions.count(),
            "status": reaction_status,
            "severity": severity,
            "reaction_types": reaction_types,
        },

        "outcomes": outcomes,
    }

def apply_haemovigilance_date_filter(
    queryset,
    start_date=None,
    end_date=None,
):
    """
    Apply inclusive date filtering using report creation date.
    """

    if start_date:
        queryset = queryset.filter(
            created_at__date__gte=start_date
        )

    if end_date:
        queryset = queryset.filter(
            created_at__date__lte=end_date
        )

    return queryset

def build_haemovigilance_time_trend(
    reports,
    period="monthly",
):
    """
    Build monthly, quarterly, or annual haemovigilance trends.
    """

    from django.db.models.functions import (
        TruncMonth,
        TruncQuarter,
        TruncYear,
    )

    if period == "monthly":
        trunc_function = TruncMonth

    elif period == "quarterly":
        trunc_function = TruncQuarter

    elif period == "annual":
        trunc_function = TruncYear

    else:
        raise ValueError(
            "Invalid period. Use monthly, quarterly, or annual."
        )

    rows = (
        reports
        .annotate(
            period_date=trunc_function(
                "created_at"
            )
        )
        .values(
            "period_date"
        )
        .annotate(
            total_reports=Count("id")
        )
        .order_by(
            "period_date"
        )
    )

    return [
        {
            "period": row["period_date"].isoformat()
            if row["period_date"]
            else None,
            "total_reports": row["total_reports"],
        }
        for row in rows
    ]

def build_reaction_time_trend(
    reports,
    period="monthly",
):
    """
    Build reaction trends by month, quarter, or year.
    """

    from django.db.models.functions import (
        TruncMonth,
        TruncQuarter,
        TruncYear,
    )

    from inventory.models_clinical import (
        TransfusionReaction,
    )

    if period == "monthly":
        trunc_function = TruncMonth

    elif period == "quarterly":
        trunc_function = TruncQuarter

    elif period == "annual":
        trunc_function = TruncYear

    else:
        raise ValueError(
            "Invalid period. Use monthly, quarterly, or annual."
        )

    reactions = TransfusionReaction.objects.filter(
        haemovigilance_report__in=reports
    )

    rows = (
        reactions
        .annotate(
            period_date=trunc_function(
                "reaction_date"
            )
        )
        .values(
            "period_date"
        )
        .annotate(
            total_reactions=Count("id")
        )
        .order_by(
            "period_date"
        )
    )

    return [
        {
            "period": row["period_date"].isoformat()
            if row["period_date"]
            else None,
            "total_reactions": row[
                "total_reactions"
            ],
        }
        for row in rows
    ]

def build_county_reporting_summary(
    reports,
):
    """
    Build county-level haemovigilance reporting summary.

    This reports counts. A true rate requires a validated
    transfusion-event denominator.
    """

    rows = (
        reports
        .values(
            "facility__county_id",
            "facility__county__name",
        )
        .annotate(
            total_reports=Count("id")
        )
        .order_by(
            "facility__county__name"
        )
    )

    return [
        {
            "county_id": row[
                "facility__county_id"
            ],
            "county_name": row[
                "facility__county__name"
            ],
            "total_reports": row[
                "total_reports"
            ],
        }
        for row in rows
    ]

def build_serious_fatal_indicators(
    reports,
):
    """
    Build serious and fatal haemovigilance indicators.
    """

    from inventory.models_clinical import (
        TransfusionReaction,
        HaemovigilanceReport,
    )

    reactions = TransfusionReaction.objects.filter(
        haemovigilance_report__in=reports
    )

    serious_reactions = reactions.filter(
        severity__in=[
            TransfusionReaction.Severity.SEVERE,
            TransfusionReaction.Severity.LIFE_THREATENING,
            TransfusionReaction.Severity.FATAL,
        ]
    )

    fatal_reactions = reactions.filter(
        severity=TransfusionReaction.Severity.FATAL
    )

    fatal_outcomes = reports.filter(
        outcome=HaemovigilanceReport.Outcome.DEATH
    )

    return {
        "serious_reactions": serious_reactions.count(),
        "fatal_reactions": fatal_reactions.count(),
        "fatal_outcomes": fatal_outcomes.count(),
    }

def build_component_analysis(
    reports,
):
    """
    Analyse transfusion reactions by blood component.
    """

    from inventory.models_clinical import (
        TransfusionReaction,
    )

    reactions = (
        TransfusionReaction.objects
        .filter(
            haemovigilance_report__in=reports
        )
        .select_related(
            "blood_issue",
            "blood_issue__inventory",
            "blood_issue__inventory__blood_unit",
        )
    )

    rows = (
        reactions
        .values(
            "blood_issue__inventory__blood_unit__component_type"
        )
        .annotate(
            total_reactions=Count("id")
        )
        .order_by(
            "blood_issue__inventory__blood_unit__component_type"
        )
    )

    return [
        {
            "component_type": row[
                "blood_issue__inventory__blood_unit__component_type"
            ],
            "total_reactions": row[
                "total_reactions"
            ],
        }
        for row in rows
    ]

def calculate_rate_per_1000(
    numerator,
    denominator,
):
    """
    Calculate an event rate per 1,000 transfused units.
    """

    if denominator <= 0:
        return None

    return round(
        (numerator / denominator) * 1000,
        2,
    )

def build_haemovigilance_rates(
    reports,
    start_date=None,
    end_date=None,
):
    """
    Calculate haemovigilance rates using completed
    transfusion events as the denominator.

    The numerator and denominator are restricted to
    the same reporting period.
    """

    from inventory.models_clinical import (
        TransfusionEvent,
        TransfusionReaction,
        HaemovigilanceReport,
    )

    # ---------------------------------------------------------
    # Completed transfusions — DENOMINATOR
    # ---------------------------------------------------------

    transfusions = TransfusionEvent.objects.filter(
        status=TransfusionEvent.Status.COMPLETED,
        facility_id__in=reports.values("facility_id"),
    )

    if start_date:
        transfusions = transfusions.filter(
            transfused_at__date__gte=start_date
        )

    if end_date:
        transfusions = transfusions.filter(
            transfused_at__date__lte=end_date
        )

    denominator = transfusions.count()

    # ---------------------------------------------------------
    # Haemovigilance reactions — NUMERATOR
    # ---------------------------------------------------------

    reactions = TransfusionReaction.objects.filter(
        haemovigilance_report__in=reports
    )

    if start_date:
        reactions = reactions.filter(
            reaction_date__date__gte=start_date
        )

    if end_date:
        reactions = reactions.filter(
            reaction_date__date__lte=end_date
        )

    total_reactions = reactions.count()

    # ---------------------------------------------------------
    # Serious reactions
    # ---------------------------------------------------------

    serious_reactions = reactions.filter(
        severity__in=[
            TransfusionReaction.Severity.SEVERE,
            TransfusionReaction.Severity.LIFE_THREATENING,
            TransfusionReaction.Severity.FATAL,
        ]
    ).count()

    # ---------------------------------------------------------
    # Fatal reactions
    # ---------------------------------------------------------

    fatal_reactions = reactions.filter(
        severity=TransfusionReaction.Severity.FATAL
    ).count()

    # ---------------------------------------------------------
    # Fatal outcomes
    # ---------------------------------------------------------

    fatal_reports = reports.filter(
        outcome=HaemovigilanceReport.Outcome.DEATH
    )

    if start_date:
        fatal_reports = fatal_reports.filter(
            created_at__date__gte=start_date
        )

    if end_date:
        fatal_reports = fatal_reports.filter(
            created_at__date__lte=end_date
        )

    fatal_outcomes = fatal_reports.count()

    return {
        "denominator": {
            "completed_transfusions": denominator,
        },

        "numerator": {
            "total_reactions": total_reactions,
            "serious_reactions": serious_reactions,
            "fatal_reactions": fatal_reactions,
            "fatal_outcomes": fatal_outcomes,
        },

        "rates_per_1000_transfused_units": {
            "total_reaction_rate": calculate_rate_per_1000(
                total_reactions,
                denominator,
            ),

            "serious_reaction_rate": calculate_rate_per_1000(
                serious_reactions,
                denominator,
            ),

            "fatal_reaction_rate": calculate_rate_per_1000(
                fatal_reactions,
                denominator,
            ),

            "fatal_outcome_rate": calculate_rate_per_1000(
                fatal_outcomes,
                denominator,
            ),
        },

        "methodology": {
            "denominator": (
                "Completed transfusion events "
                "within the reporting period."
            ),
            "rate_multiplier": 1000,
            "zero_denominator": (
                "Rate is null when no completed "
                "transfusion events exist."
            ),
        },
    }