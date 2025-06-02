import requests, xml.etree.ElementTree as ET
from django.conf import settings
from django.db import transaction
from agendas.models import Bill
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def fetch_and_store_bills(p_size: int = 100):
    """
    20·21·22대 모든 의안을 누락 없이 수집해 Bill 테이블에 저장
    반환값: 새로 저장된 건수
    """
    key = settings.ASSEMBLY_API_KEY
    base_url = "https://open.assembly.go.kr/portal/openapi/nwbpacrgavhjryiph"

    # ── 1. 중복 확인을 위한 기존 bill_id 로드 ──
    existing_ids = set(Bill.objects.values_list("bill_id", flat=True))

    # ── 2. 재시도 설정된 세션 ──
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://",  HTTPAdapter(max_retries=retry))

    saved = 0  # 최종 저장 건수

    for age in range(20, 23):           # 20·21·22대
        page = 1
        while True:
            url = f"{base_url}?KEY={key}&AGE={age}&pIndex={page}&pSize={p_size}"
            try:
                resp = session.get(url, timeout=10)
                resp.raise_for_status()
                resp.encoding = "utf-8"
                root = ET.fromstring(resp.text)
            except Exception as e:
                print(f"[ERROR] AGE {age} page {page}: {e}")
                break  # 심각한 오류 → 다음 AGE로

            rows = root.findall(".//row")
            if not rows:
                break  # 더 이상 데이터 없음

            new_objs = []
            for row in rows:
                bill_id = row.findtext("BILL_ID")
                if not bill_id or bill_id in existing_ids:
                    continue
                existing_ids.add(bill_id)

                new_objs.append(
                    Bill(
                        bill_no=row.findtext("BILL_NO"),
                        age=row.findtext("AGE"),
                        bill_name=row.findtext("BILL_NM"),
                        bill_kind=row.findtext("BILL_KIND"),
                        proposer=row.findtext("PROPOSER"),
                        rgs_proc_dt=row.findtext("RGS_PROC_DT"),
                        committee=row.findtext("COMMITTEE_NM"),
                        proc_result=row.findtext("PROC_RESULT_CD"),
                        bill_id=bill_id,
                    )
                )

            # ── 3. bulk_create 단위 저장 ──
            if new_objs:
                try:
                    with transaction.atomic():
                        Bill.objects.bulk_create(new_objs, batch_size=p_size)
                    saved += len(new_objs)
                except Exception as e:
                    print(f"[SAVE ERROR] AGE {age} page {page}: {e}")

            # ── 4. 마지막 페이지 판정 ──
            if len(rows) < p_size:
                break  # 현재 AGE 완료
            page += 1

    print(f"[SUMMARY] Total new bills saved: {saved}")
    return saved
