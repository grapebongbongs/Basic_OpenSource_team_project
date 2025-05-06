import requests
import xml.etree.ElementTree as ET
import time

from agendas.models import Bill
from members.models import AssemblyMember
from vote.models import Vote
from django.conf import settings

def fetch_and_store_votes():
    key = settings.ASSEMBLY_API_KEY
    url = 'https://open.assembly.go.kr/portal/openapi/nojepdqqaweusdfbi'
    saved_count = 0

    for age in range(20, 23):  # 20~22대 반복
        bills = Bill.objects.filter(age=str(age))

        for bill in bills:
            bill_id = bill.bill_id
            full_url = f"{url}?KEY={key}&AGE={age}&BILL_ID={bill_id}&type=xml"

            try:
                res = requests.get(full_url, timeout=10)
                res.raise_for_status()
                time.sleep(0.3)
            except requests.exceptions.RequestException:
                continue

            root = ET.fromstring(res.text)
            rows = root.findall('row')

            for row in rows:
                mona_cd = row.findtext('MONA_CD')
                vote_result = row.findtext('RESULT_VOTE_MOD')

                if not vote_result:
                    continue

                try:
                    member = AssemblyMember.objects.get(mona_cd=mona_cd)
                    if not Vote.objects.filter(bill=bill, member=member).exists():
                        Vote.objects.create(
                            bill=bill,
                            member=member,
                            vote_result=vote_result
                        )
                        saved_count += 1

                        if saved_count % 500 == 0:
                            print(f"✅ {saved_count}건 저장 완료")

                except AssemblyMember.DoesNotExist:
                    continue

    print(f"\n🎉 최종 저장된 표결 수: {saved_count}")
    return saved_count