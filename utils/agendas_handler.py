import requests
import xml.etree.ElementTree as ET
from agendas.models import Bill
from django.conf import settings

def fetch_and_store_bills():
    key = settings.ASSEMBLY_API_KEY
    base_url = 'https://open.assembly.go.kr/portal/openapi/nwbpacrgavhjryiph'
    pSize = 100
    count = 0

    for AGE in range(20, 23):
        pIndex = 1  # ← 위치 중요
        while True:
            url = f'{base_url}?KEY={key}&AGE={AGE}&pIndex={pIndex}&pSize={pSize}'
            res = requests.get(url)
            res.encoding = 'utf-8'
            root = ET.fromstring(res.text)
            rows = root.findall('row')
            if not rows:
                break

            for row in rows:
                bill_id = row.findtext('BILL_ID')
                if not bill_id or Bill.objects.filter(bill_id=bill_id).exists():
                    continue
                Bill.objects.create(
                    bill_no=row.findtext('BILL_NO'),
                    age=row.findtext('AGE'),
                    bill_name=row.findtext('BILL_NM'),
                    bill_kind=row.findtext('BILL_KIND'),
                    proposer=row.findtext('PROPOSER'),
                    rgs_proc_dt=row.findtext('RGS_PROC_DT'),
                    committee=row.findtext('COMMITTEE_NM'),
                    proc_result=row.findtext('PROC_RESULT_CD'),
                    bill_id=bill_id,
                )
                count += 1  # ← 저장된 건수 증가
            pIndex += 1

    return count