import requests
import xml.etree.ElementTree as ET
from agendas.models import Bill
from django.conf import settings

def fetch_and_store_bills():
    key = settings.ASSEMBLY_API_KEY
    base_url = 'https://open.assembly.go.kr/portal/openapi/nwbpacrgavhjryiph'
    pIndex = 1
    pSize = 100
    count = 0
    AGE = 21

    while True:
        url = f'{base_url}?KEY={key}&AGE={AGE}&pIndex={pIndex}&pSize={pSize}'
        res = requests.get(url)
        res.encoding = 'utf-8'
        root = ET.fromstring(res.text)
        rows = root.findall('row')
        if not rows:
            break

        for row in rows:
            bill_no = row.findtext('BILL_NO')
            if not bill_no or Bill.objects.filter(bill_no=bill_no).exists():
                continue
            Bill.objects.create(
                bill_no=bill_no,
                age=row.findtext('AGE'),
                bill_name=row.findtext('BILL_NM'),
                bill_kind=row.findtext('BILL_KIND'),
                proposer=row.findtext('PROPOSER'),
                propose_dt=row.findtext('PROPOSE_DT'),
                committee=row.findtext('COMMITTEE_NM'),
                proc_result=row.findtext('PROC_RESULT_CD'),
            )
            count += 1
        pIndex += 1

    return count
