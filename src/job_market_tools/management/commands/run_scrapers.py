# src/job_market_tools/management/commands/run_scrapers.py
from django.core.management.base import BaseCommand
from job_market_tools.scraper.manager import ScraperManager

class Command(BaseCommand):
    help = "Start up your scrapers"

    def handle(self, *args, **options):
        mgr = ScraperManager()
        mgr.register("justjoin")
        mgr.start("justjoin", 10)
        self.stdout.write("Scraper started. Ctrl-C to stop.")
        try:
            while True:
                pass
        except KeyboardInterrupt:
            self.stdout.write("\nStopping…")
            mgr.stop("justjoin")
