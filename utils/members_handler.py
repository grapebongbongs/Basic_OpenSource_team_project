import requests
import xml.etree.ElementTree as ET
from members.models import AssemblyMember
from django.conf import settings

def fetch_and_store_members():  # 국회의원 인적사항 api에서 가져오는 국회의원 정보 저장 (현재 국회의원만만)
    key = settings.ASSEMBLY_API_KEY
    url = 'https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu'
    pIndex = 1
    pSize = 100
    count = 0

    while True:
        full_url = f'{url}?KEY={key}&pIndex={pIndex}&pSize={pSize}'
        res = requests.get(full_url)
        res.encoding = 'utf-8'
        root = ET.fromstring(res.text)
        rows = root.findall('row')
        if not rows:
            break

        for row in rows:
            mona_cd = row.findtext('MONA_CD')
            if not AssemblyMember.objects.filter(mona_cd=mona_cd).exists():
                AssemblyMember.objects.create(
                    mona_cd=mona_cd,
                    name=row.findtext('HG_NM'),
                    party=row.findtext('POLY_NM'),
                    committee=row.findtext('CMIT_NM'),
                    position=row.findtext('JOB_RES_NM'),
                    elect_gbn=row.findtext('ELECT_GBN_NM'),
                    origin=row.findtext('ORIG_NM'),
                    email=row.findtext('E_MAIL'),
                    phone=row.findtext('TEL_NO'),
                    homepage=row.findtext('HOMEPAGE'),
                    unit=row.findtext('UNITS'),
                    title=row.findtext('MEM_TITLE'),
                )
                count += 1
        pIndex += 1

    return count


def fetch_and_store_member_images():  #국회의원 통합정보 api에서 가져오는 국회의원 이미지 링크 저장
    key = settings.ASSEMBLY_API_KEY
    url = 'https://open.assembly.go.kr/portal/openapi/ALLNAMEMBER'
    pIndex = 1
    pSize = 100
    update_count = 0

    while True:
        full_url = f'{url}?KEY={key}&type=xml&pIndex={pIndex}&pSize={pSize}'
        res = requests.get(full_url)
        res.encoding = 'utf-8'
        root = ET.fromstring(res.text)
        items = root.findall('row')
        if not items:
            break

        for item in items:
            naas_cd = item.findtext('NAAS_CD')
            jpg_link = item.findtext('NAAS_PIC')
            if naas_cd and jpg_link:
                try:
                    member = AssemblyMember.objects.get(mona_cd=naas_cd)
                    member.image_url = jpg_link
                    member.save()
                    update_count += 1
                except AssemblyMember.DoesNotExist:
                    continue
        pIndex += 1

    return update_count



def fetch_all_members_and_images():  # 국회의원 인적사항과 이미지 링크를 모두 가져와서 저장하고, 저장한 데이터의 개수를 저장하는 함수
    member_count = fetch_and_store_members()
    image_count = fetch_and_store_member_images()
    return member_count, image_count


