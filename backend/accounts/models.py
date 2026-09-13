from django.contrib.auth.models import AbstractUser
from django.db import models
from facilities.models import Facility

class User(AbstractUser):

    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Administrator"
        NATIONAL_ADMIN = "NATIONAL_ADMIN", "National Administrator"
        REGIONAL_ADMIN = "REGIONAL_ADMIN", "Regional Administrator"
        COUNTY_ADMIN = "COUNTY_ADMIN", "County Administrator"
        FACILITY_ADMIN = "FACILITY_ADMIN", "Facility Administrator"
        BLOOD_BANK_OFFICER = "BLOOD_BANK_OFFICER", "Blood Bank Officer"
        LABORATORY_OFFICER = "LABORATORY_OFFICER", "Laboratory Officer"
        INVENTORY_OFFICER = "INVENTORY_OFFICER", "Inventory Officer"
        CLINICIAN = "CLINICIAN", "Clinician"
        RMNCAH_OFFICER = "RMNCAH_OFFICER", "RMNCAH Officer"
        DATA_OFFICER = "DATA_OFFICER", "Data Officer"
        AUDITOR = "AUDITOR", "Auditor"

    role = models.CharField(
        max_length=50,
        choices=Role.choices,
        default=Role.FACILITY_ADMIN,
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    facility = models.ForeignKey(
        Facility,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"