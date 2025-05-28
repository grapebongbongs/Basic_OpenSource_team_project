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
                    staff=row.findtext('STAFF'),
                    secretary=row.findtext('SECRETARY'),
                    assem_addr=row.findtext('ASSEM_ADDR'),
                    hj_nm=row.findtext('HJ_NM'),  
                )
                count += 1
        pIndex += 1

    return count

def fetch_and_update_members_by_unit_cd(unit_cds=[100020, 100021]):
    key = settings.ASSEMBLY_API_KEY
    base_url = 'https://open.assembly.go.kr/portal/openapi/npffdutiapkzbfyvr'
    update_count = 0
    create_count = 0

    for unit_cd in unit_cds:
        pIndex = 1
        pSize = 100

        while True:
            full_url = f"{base_url}?KEY={key}&type=xml&UNIT_CD={unit_cd}&pIndex={pIndex}&pSize={pSize}"
            try:
                res = requests.get(full_url, timeout=10)
                res.encoding = 'utf-8'
                root = ET.fromstring(res.text)
                rows = root.findall('row')
                if not rows:
                    break

                for row in rows:
                    mona_cd = row.findtext('MONA_CD')
                    if not mona_cd:
                        continue

                    member = AssemblyMember.objects.filter(mona_cd=mona_cd).first()

                    if member:
                        # ✅ 기존 객체: UNIT_CD만 누적
                        current_unit_cds = member.unit_cd.split(',') if member.unit_cd else []
                        if str(unit_cd) not in current_unit_cds:
                            current_unit_cds.append(str(unit_cd))
                            member.unit_cd = ','.join(sorted(set(current_unit_cds)))
                            member.save()
                            update_count += 1

                    else:
                        # ✅ 신규 객체: 모든 정보 저장
                        AssemblyMember.objects.create(
                            mona_cd=mona_cd,
                            name=row.findtext('HG_NM'),
                            hj_nm=row.findtext('HJ_NM'),
                            unit=row.findtext('UNITS'),
                            unit_cd=str(unit_cd),
                            origin=row.findtext('ORIG_NM'),
                            elect_gbn=row.findtext('ELECT_GBN_NM'),
                            party=row.findtext('POLY_NM')
                        )
                        create_count += 1

                pIndex += 1

            except Exception as e:
                print(f"❌ API 실패: UNIT_CD={unit_cd}, pIndex={pIndex}, 이유: {e}")
                break

    print(f"🆕 신규 의원 {create_count}명 생성")
    print(f"🔁 기존 의원 {update_count}명에 UNIT_CD 업데이트")
    return create_count + update_count


def fetch_and_store_member_images():
    """
    ALLNAMEMBER API를 통해 AssemblyMember 전체에 대해 이미지 및 committee 정보 저장
    - mona_cd 기준으로 AssemblyMember를 찾고, image_url과 committee를 채움
    """
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
        rows = root.findall('row')
        if not rows:
            break

        for row in rows:
            mona_cd = row.findtext('NAAS_CD')
            image_url = row.findtext('NAAS_PIC')
            committee = row.findtext('CMIT_NM')

            if not mona_cd:
                continue

            try:
                member = AssemblyMember.objects.get(mona_cd=mona_cd)

                updated = False
                if image_url and not member.image_url:
                    member.image_url = image_url
                    updated = True

                if committee and not member.committee:
                    member.committee = committee
                    updated = True

                if updated:
                    member.save()
                    update_count += 1

            except AssemblyMember.DoesNotExist:
                continue

        pIndex += 1

    return update_count


def fetch_all_members_and_images():
    member_count = fetch_and_store_members()
    patch_count = fetch_and_update_members_by_unit_cd(unit_cds=[100020, 100021])
    image_count = fetch_and_store_member_images()
    return member_count, patch_count, image_count


