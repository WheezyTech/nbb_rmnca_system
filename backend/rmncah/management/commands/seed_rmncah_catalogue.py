from django.core.management.base import BaseCommand

from rmncah.models import (
    RMNCAHService,
    RMNCAHServiceCategory,
)


CATEGORIES = [
    {
        "code": "MATERNAL",
        "name": "Maternal Health",
        "category_type": "MATERNAL",
        "description": "Maternal health services.",
        "display_order": 10,
    },
    {
        "code": "ANC",
        "name": "Antenatal Care",
        "category_type": "ANC",
        "description": "Antenatal and pregnancy care services.",
        "display_order": 20,
    },
    {
        "code": "MATERNITY",
        "name": "Maternity Services",
        "category_type": "MATERNITY",
        "description": "Labour, delivery and maternity services.",
        "display_order": 30,
    },
    {
        "code": "PNC",
        "name": "Postnatal Care",
        "category_type": "PNC",
        "description": "Postnatal services for mothers and newborns.",
        "display_order": 40,
    },
    {
        "code": "NEWBORN",
        "name": "Newborn Health",
        "category_type": "NEWBORN",
        "description": "Newborn care and neonatal services.",
        "display_order": 50,
    },
    {
        "code": "CHILD",
        "name": "Child Health",
        "category_type": "CHILD",
        "description": "Child health services.",
        "display_order": 60,
    },
    {
        "code": "ADOLESCENT",
        "name": "Adolescent Health",
        "category_type": "ADOLESCENT",
        "description": "Adolescent and youth health services.",
        "display_order": 70,
    },
    {
        "code": "FAMILY_PLANNING",
        "name": "Family Planning",
        "category_type": "FAMILY_PLANNING",
        "description": "Family planning and contraceptive services.",
        "display_order": 80,
    },
    {
        "code": "REPRODUCTIVE",
        "name": "Reproductive Health",
        "category_type": "REPRODUCTIVE",
        "description": "Reproductive health services.",
        "display_order": 90,
    },
    {
        "code": "IMMUNIZATION",
        "name": "Immunization",
        "category_type": "IMMUNIZATION",
        "description": "Routine immunization services.",
        "display_order": 100,
    },
]


SERVICES = [
    (
        "ANC-001",
        "Antenatal Care - First Visit",
        "ANC",
        True,
        False,
        False,
    ),
    (
        "ANC-002",
        "Antenatal Care - Follow-up",
        "ANC",
        True,
        False,
        False,
    ),
    (
        "ANC-003",
        "High-Risk Pregnancy Assessment",
        "ANC",
        True,
        True,
        True,
    ),
    (
        "MAT-001",
        "Normal Delivery",
        "MATERNITY",
        True,
        False,
        True,
    ),
    (
        "MAT-002",
        "Emergency Obstetric Care",
        "MATERNITY",
        True,
        True,
        True,
    ),
    (
        "MAT-003",
        "Caesarean Section",
        "MATERNITY",
        True,
        True,
        True,
    ),
    (
        "PNC-001",
        "Maternal Postnatal Care",
        "PNC",
        True,
        False,
        False,
    ),
    (
        "PNC-002",
        "Newborn Postnatal Care",
        "PNC",
        True,
        False,
        False,
    ),
    (
        "NB-001",
        "Essential Newborn Care",
        "NEWBORN",
        True,
        False,
        False,
    ),
    (
        "NB-002",
        "Neonatal Emergency Care",
        "NEWBORN",
        True,
        True,
        True,
    ),
    (
        "CH-001",
        "Child Welfare Services",
        "CHILD",
        True,
        False,
        False,
    ),
    (
        "CH-002",
        "Growth Monitoring",
        "CHILD",
        True,
        False,
        False,
    ),
    (
        "CH-003",
        "Integrated Child Health",
        "CHILD",
        True,
        False,
        False,
    ),
    (
        "ADO-001",
        "Adolescent Health Services",
        "ADOLESCENT",
        True,
        False,
        False,
    ),
    (
        "FP-001",
        "Family Planning Counselling",
        "FAMILY_PLANNING",
        True,
        False,
        False,
    ),
    (
        "FP-002",
        "Contraceptive Services",
        "FAMILY_PLANNING",
        True,
        False,
        False,
    ),
    (
        "RH-001",
        "Reproductive Health Consultation",
        "REPRODUCTIVE",
        True,
        False,
        False,
    ),
    (
        "RH-002",
        "Cervical Cancer Screening",
        "REPRODUCTIVE",
        True,
        False,
        False,
    ),
    (
        "RH-003",
        "STI/RTI Services",
        "REPRODUCTIVE",
        True,
        False,
        False,
    ),
    (
        "IMM-001",
        "Routine Immunization",
        "IMMUNIZATION",
        True,
        False,
        False,
    ),
]


class Command(BaseCommand):
    help = "Seed the national RMNCAH service catalogue."

    def handle(self, *args, **options):

        category_map = {}

        for data in CATEGORIES:
            category, created = (
                RMNCAHServiceCategory.objects.update_or_create(
                    code=data["code"],
                    defaults={
                        "name": data["name"],
                        "category_type": data["category_type"],
                        "description": data["description"],
                        "display_order": data["display_order"],
                        "is_active": True,
                    },
                )
            )

            category_map[data["code"]] = category

            action = "Created" if created else "Updated"

            self.stdout.write(
                self.style.SUCCESS(
                    f"{action} category: {category.code}"
                )
            )

        for index, (
            code,
            name,
            category_code,
            clinical_staff,
            referral,
            emergency,
        ) in enumerate(SERVICES, start=1):

            category = category_map[category_code]

            service, created = (
                RMNCAHService.objects.update_or_create(
                    code=code,
                    defaults={
                        "category": category,
                        "name": name,
                        "requires_clinical_staff": clinical_staff,
                        "requires_referral": referral,
                        "is_emergency_service": emergency,
                        "is_active": True,
                        "display_order": index,
                    },
                )
            )

            action = "Created" if created else "Updated"

            self.stdout.write(
                self.style.SUCCESS(
                    f"{action} service: {service.code}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "RMNCAH catalogue successfully seeded."
            )
        )