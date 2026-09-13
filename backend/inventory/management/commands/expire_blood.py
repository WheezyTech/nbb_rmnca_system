from django.core.management.base import BaseCommand

from inventory.services.transactions import (
    expire_blood_units,
)


class Command(BaseCommand):

    help = "Mark expired blood units as expired."

    def handle(self, *args, **options):

        count = expire_blood_units()

        self.stdout.write(
            self.style.SUCCESS(
                f"{count} blood unit(s) marked as expired."
            )
        )