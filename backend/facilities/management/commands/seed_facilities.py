from django.core.management.base import BaseCommand

from facilities.models import Region, County


class Command(BaseCommand):
    help = "Create initial regions and counties"

    def handle(self, *args, **options):

        regions_data = {
            "Central": "CEN",
            "Coast": "CST",
            "Eastern": "EST",
            "Nairobi": "NBI",
            "North Eastern": "NER",
            "Nyanza": "NYA",
            "Rift Valley": "RVT",
            "Western": "WST",
        }

        regions = {}

        for name, code in regions_data.items():
            region, created = Region.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "is_active": True,
                },
            )

            regions[name] = region

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created region: {name}"
                    )
                )

        counties_data = {
            "Central": [
                ("Kiambu", "KIA"),
                ("Murang'a", "MUR"),
                ("Kirinyaga", "KIR"),
                ("Nyeri", "NYE"),
                ("Nyandarua", "NYA"),
            ],

            "Coast": [
                ("Mombasa", "MOM"),
                ("Kwale", "KWA"),
                ("Kilifi", "KLF"),
                ("Tana River", "TAR"),
                ("Lamu", "LAM"),
                ("Taita Taveta", "TTV"),
            ],

            "Eastern": [
                ("Machakos", "MAC"),
                ("Kitui", "KIT"),
                ("Embu", "EMB"),
                ("Tharaka Nithi", "THN"),
                ("Meru", "MER"),
                ("Isiolo", "ISL"),
                ("Marsabit", "MSB"),
            ],

            "Nairobi": [
                ("Nairobi", "NBI"),
            ],

            "North Eastern": [
                ("Garissa", "GAR"),
                ("Wajir", "WAJ"),
                ("Mandera", "MAN"),
            ],

            "Nyanza": [
                ("Kisumu", "KSM"),
                ("Siaya", "SIA"),
                ("Kisii", "KII"),
                ("Nyamira", "NYM"),
                ("Homa Bay", "HBY"),
                ("Migori", "MIG"),
            ],

            "Rift Valley": [
                ("Nakuru", "NAK"),
                ("Narok", "NRK"),
                ("Kajiado", "KAJ"),
                ("Kericho", "KER"),
                ("Bomet", "BOM"),
                ("Baringo", "BAR"),
                ("Laikipia", "LAI"),
                ("Samburu", "SAM"),
                ("Trans Nzoia", "TNZ"),
                ("Uasin Gishu", "UGI"),
                ("Elgeyo Marakwet", "ELM"),
                ("Nandi", "NAN"),
                ("West Pokot", "WPO"),
                ("Turkana", "TUR"),
            ],

            "Western": [
                ("Kakamega", "KAK"),
                ("Vihiga", "VIH"),
                ("Bungoma", "BUN"),
                ("Busia", "BUS"),
            ],
        }

        for region_name, counties in counties_data.items():

            region = regions[region_name]

            for county_name, county_code in counties:

                county, created = County.objects.get_or_create(
                    code=county_code,
                    defaults={
                        "name": county_name,
                        "region": region,
                        "is_active": True,
                    },
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Created county: {county_name}"
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                "Initial regions and counties loaded successfully."
            )
        )