from django.core.management.base import BaseCommand

from marketplace.models import Region
from pages.regions import NER_PLACES

class Command(BaseCommand):
    help = "Create or update Region rows from pages/regions.py"

    def handle(self, *args, **options):
        created = 0
        for state, places in NER_PLACES.items():
            for name, lat, lon in places:
                _, was_created = Region.objects.update_or_create(
                    name=name,
                    state=state,
                    defaults={"latitude": lat, "longitude": lon},
                )
                created += was_created
        self.stdout.write(self.style.SUCCESS(f"Done: {created} new regions."))
