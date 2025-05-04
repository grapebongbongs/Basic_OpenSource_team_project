from django.core.management.base import BaseCommand
from utils.agendas_handler import fetch_and_store_bills

class Command(BaseCommand):
    help = 'Fetch and store bill data from National Assembly API'

    def handle(self, *args, **kwargs):
        added = fetch_and_store_bills()
        self.stdout.write(self.style.SUCCESS(f'{added} bill records added.'))