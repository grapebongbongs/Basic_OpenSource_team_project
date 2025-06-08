from django.core.management.base import BaseCommand
from utils.members_handler import fetch_all_members_and_images

class Command(BaseCommand):
    help = "국회의원 정보 및 이미지 링크 저장"

    def handle(self, *args, **kwargs):
        member_count, patch_count, image_count = fetch_all_members_and_images()
        self.stdout.write(self.style.SUCCESS(f'{member_count}명 의원 정보 저장 완료'))
        self.stdout.write(self.style.SUCCESS(f'{image_count}명 이미지 링크 저장 완료'))
        self.stdout.write(self.style.SUCCESS(f'{patch_count}명 역대 의원 정보 저장 완료'))