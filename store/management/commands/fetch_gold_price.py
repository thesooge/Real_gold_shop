# store/management/commands/fetch_gold_price.py
from django.core.management.base import BaseCommand
from store.cron import fetch_gold_price  # or from store.services import ...

class Command(BaseCommand):
    help = "Fetch latest gold price from BRS API and save to DB"

    def handle(self, *args, **options):
        fetch_gold_price()
        self.stdout.write(self.style.SUCCESS("Gold price fetched."))