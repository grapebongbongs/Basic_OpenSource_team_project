from django.core.management.base import BaseCommand
from utils.vote_handler import fetch_and_store_votes

class Command(BaseCommand):
    help = "국회의원 표결 정보 저장 (20~22대 전체)"

    def handle(self, *args, **kwargs):
        count = fetch_and_store_votes()
        self.stdout.write(self.style.SUCCESS(f"{count}개의 표결 정보 저장 완료"))