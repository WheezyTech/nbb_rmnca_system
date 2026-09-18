from django.core.exceptions import ValidationError
from django.db import transaction

from .models_anc import (
    ANCClient,
    PregnancyRecord,
    ANCVisit,
    ANCRiskAssessment,
    ANCInvestigation,
    ANCReferral,
    ANCClinicalEvent,
)


def create_anc_event(
    pregnancy,
    facility,
    event_type,
    performed_by,
    description="",
    metadata=None,
):
    return ANCClinicalEvent.objects.create(
        pregnancy=pregnancy,
        facility=facility,
        event_type=event_type,
        performed_by=performed_by,
        description=description,
        metadata=metadata or {},
    )


@transaction.atomic
def register_anc_client(
    facility,
    registered_by,
    patient_reference,
    first_name,
    last_name,
    **kwargs,
):
    if ANCClient.objects.filter(
        facility=facility,
        patient_reference=patient_reference,
    ).exists():
        raise ValidationError(
            "An ANC client with this patient reference already exists "
            "at this facility."
        )

    client = ANCClient.objects.create(
        facility=facility,
        registered_by=registered_by,
        patient_reference=patient_reference,
        first_name=first_name,
        last_name=last_name,
        **kwargs,
    )

    return client


@transaction.atomic
def create_pregnancy(
    client,
    created_by,
    **kwargs,
):
    if client.status != ANCClient.Status.ACTIVE:
        raise ValidationError(
            "This ANC client is not active."
        )

    active_pregnancy = PregnancyRecord.objects.filter(
        client=client,
        status=PregnancyRecord.Status.ACTIVE,
    ).exists()

    if active_pregnancy:
        raise ValidationError(
            "The client already has an active pregnancy."
        )

    pregnancy = PregnancyRecord.objects.create(
        client=client,
        facility=client.facility,
        created_by=created_by,
        **kwargs,
    )

    create_anc_event(
        pregnancy=pregnancy,
        facility=client.facility,
        event_type=ANCClinicalEvent.EventType.PREGNANCY_CREATED,
        performed_by=created_by,
        description="Pregnancy record created.",
    )

    return pregnancy


@transaction.atomic
def complete_anc_visit(
    pregnancy,
    attended_by,
    **kwargs,
):
    if pregnancy.status != PregnancyRecord.Status.ACTIVE:
        raise ValidationError(
            "ANC visits can only be recorded for an active pregnancy."
        )

    visit_number = (
        ANCVisit.objects.filter(
            pregnancy=pregnancy
        ).count()
        + 1
    )

    visit = ANCVisit.objects.create(
        pregnancy=pregnancy,
        facility=pregnancy.facility,
        attended_by=attended_by,
        visit_number=visit_number,
        **kwargs,
    )

    create_anc_event(
        pregnancy=pregnancy,
        facility=pregnancy.facility,
        event_type=ANCClinicalEvent.EventType.VISIT_COMPLETED,
        performed_by=attended_by,
        description=f"ANC visit {visit_number} completed.",
        metadata={
            "visit_id": visit.visit_id,
            "visit_number": visit_number,
        },
    )

    return visit


@transaction.atomic
def assess_anc_risk(
    pregnancy,
    assessed_by,
    **kwargs,
):
    assessment = ANCRiskAssessment.objects.create(
        pregnancy=pregnancy,
        facility=pregnancy.facility,
        assessed_by=assessed_by,
        **kwargs,
    )

    if assessment.risk_level in {
        ANCRiskAssessment.RiskLevel.HIGH,
        ANCRiskAssessment.RiskLevel.CRITICAL,
    }:
        pregnancy.high_risk = True
        pregnancy.risk_summary = assessment.risk_factors
        pregnancy.save(
            update_fields=[
                "high_risk",
                "risk_summary",
                "updated_at",
            ]
        )

    create_anc_event(
        pregnancy=pregnancy,
        facility=pregnancy.facility,
        event_type=ANCClinicalEvent.EventType.RISK_ASSESSED,
        performed_by=assessed_by,
        description=(
            f"ANC risk assessed as "
            f"{assessment.get_risk_level_display()}."
        ),
        metadata={
            "assessment_id": assessment.assessment_id,
            "risk_level": assessment.risk_level,
            "referral_required": assessment.referral_required,
        },
    )

    return assessment


@transaction.atomic
def create_anc_investigation(
    pregnancy,
    ordered_by,
    **kwargs,
):
    investigation = ANCInvestigation.objects.create(
        pregnancy=pregnancy,
        facility=pregnancy.facility,
        ordered_by=ordered_by,
        **kwargs,
    )

    create_anc_event(
        pregnancy=pregnancy,
        facility=pregnancy.facility,
        event_type=ANCClinicalEvent.EventType.INVESTIGATION_ORDERED,
        performed_by=ordered_by,
        description=(
            f"Investigation ordered: {investigation.test_name}."
        ),
        metadata={
            "investigation_id": investigation.investigation_id,
            "test_name": investigation.test_name,
        },
    )

    return investigation


@transaction.atomic
def create_anc_referral(
    pregnancy,
    referred_by,
    to_facility,
    reason,
    **kwargs,
):
    if to_facility.id == pregnancy.facility_id:
        raise ValidationError(
            "Referral destination must be different from "
            "the current facility."
        )

    referral = ANCReferral.objects.create(
        pregnancy=pregnancy,
        from_facility=pregnancy.facility,
        to_facility=to_facility,
        referred_by=referred_by,
        reason=reason,
        **kwargs,
    )

    create_anc_event(
        pregnancy=pregnancy,
        facility=pregnancy.facility,
        event_type=ANCClinicalEvent.EventType.REFERRAL_CREATED,
        performed_by=referred_by,
        description="ANC referral created.",
        metadata={
            "referral_id": referral.referral_id,
            "to_facility_id": to_facility.id,
            "urgency": referral.urgency,
        },
    )

    return referral