import requests
import xml.etree.ElementTree as ET
import time

from django.db import transaction
from django.conf import settings

from agendas.models import Bill
from members.models import AssemblyMember
from vote.models import Vote

def fetch_and_store_votes():
    key = settings.ASSEMBLY_API_KEY
    url = 'https://open.assembly.go.kr/portal/openapi/nojepdqqaweusdfbi'
    saved_count = 0
    MAX_RETRY = 3
    batch_size = 300
    vote_buffer = []
    failed_bills = []

    # ✅ AssemblyMember 캐싱 (속도 향상)
    member_map = {m.mona_cd: m for m in AssemblyMember.objects.all()}

    for age in range(20, 23):  # 20 ~ 22대 국회
        bills = Bill.objects.filter(age=str(age))

        for bill in bills:
            bill_id = bill.bill_id
            retry_count = 0

            while retry_count < MAX_RETRY:
                try:
                    full_url = f"{url}?KEY={key}&AGE={age}&BILL_ID={bill_id}&type=xml"
                    res = requests.get(full_url, timeout=10)
                    res.raise_for_status()
                    time.sleep(0.3)
                    break
                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    print(f"⚠️ 요청 실패: BILL_ID={bill_id}, 재시도 {retry_count}/3 - 에러: {e}")
                    time.sleep(1)

            if retry_count == MAX_RETRY:
                failed_bills.append(bill_id)
                continue

            try:
                root = ET.fromstring(res.text)
            except ET.ParseError as e:
                print(f"❌ XML 파싱 실패: BILL_ID={bill_id}, 에러: {e}")
                failed_bills.append(bill_id)
                continue

            rows = root.findall('row')
            if not rows:
                print(f"ℹ️ 표결 없음: BILL_ID={bill_id}")
                continue

            # ✅ 중복 체크: (bill_id, mona_cd) 조합으로 구성
            existing_votes = set(
                Vote.objects.filter(bill=bill).values_list('bill_id', 'member__mona_cd')
            )

            for row in rows:
                mona_cd = row.findtext('MONA_CD')
                vote_result = row.findtext('RESULT_VOTE_MOD')

                if not mona_cd or not vote_result:
                    continue

                if (bill.bill_id, mona_cd) in existing_votes:
                    continue

                member = member_map.get(mona_cd)
                if not member:
                    continue

                vote_buffer.append(Vote(
                    bill=bill,
                    member=member,
                    vote_result=vote_result
                ))
                saved_count += 1

                if len(vote_buffer) >= batch_size:
                    with transaction.atomic():
                        Vote.objects.bulk_create(vote_buffer)
                    print(f"✅ {len(vote_buffer)}건 저장 완료")
                    vote_buffer.clear()

    # 마지막 남은 버퍼 저장
    if vote_buffer:
        with transaction.atomic():
            Vote.objects.bulk_create(vote_buffer)
        print(f"✅ 최종 {len(vote_buffer)}건 추가 저장 완료")

    print(f"\n🎉 최종 저장된 표결 수: {saved_count}")
    if failed_bills:
        print(f"❗ 실패한 BILL_ID 목록 ({len(failed_bills)}건): {failed_bills}")

    return saved_count

