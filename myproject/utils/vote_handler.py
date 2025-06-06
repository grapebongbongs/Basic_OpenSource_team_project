import requests, xml.etree.ElementTree as ET, time
from collections import defaultdict

from django.db import transaction
from django.conf import settings

from agendas.models import Bill
from members.models import AssemblyMember
from vote.models import Vote


API           = "https://open.assembly.go.kr/portal/openapi/nojepdqqaweusdfbi"
MAX_RETRY     = 3
P_SIZE        = 1000       # 페이지당 행 수
BATCH_SIZE    = 500        # bulk_create 단위
CONCURRENCY_PS= 0.15       # API 완충(seconds)

# ────────────────────────────────────────────
def tag(elem, *names):
    """네임스페이스 무시 .findtext() 헬퍼"""
    for n in names:
        v = elem.findtext(n) or elem.findtext(f".//{{*}}{n}")
        if v:
            return v.strip()
    return None
# ────────────────────────────────────────────
def flush_votes(buf, total_saved):
    """버퍼를 DB에 저장하고 진행률 출력"""
    if not buf:
        return 0
    with transaction.atomic():
        Vote.objects.bulk_create(buf, batch_size=BATCH_SIZE, ignore_conflicts=True)
    batch_n = len(buf)
    total_saved += batch_n
    print(f"  ↳ {batch_n:,}건 저장 (누적 {total_saved:,})")
    return total_saved
# ────────────────────────────────────────────
def fetch_and_store_votes_progress():
    key = settings.ASSEMBLY_API_KEY

    # 의원 캐싱
    member_map   = {m.mona_cd: m for m in AssemblyMember.objects.all()}
    # 표결 중복 집합 (의안별)
    existing_all = defaultdict(set)
    buf          = []
    saved_total  = 0
    failed_bills = []
    missing_mem  = defaultdict(int)

    for age in range(20, 23):                                  # 20~22대
        bills = Bill.objects.filter(age=age)
        for bill in bills:
            bill_id = bill.bill_id
            existing = existing_all[bill_id]                    # 셋
            page     = 1

            while True:                                         # 페이지 루프
                full = (f"{API}?KEY={key}&AGE={age}&BILL_ID={bill_id}"
                        f"&pIndex={page}&pSize={P_SIZE}&type=xml")

                # ---- HTTP 재시도 ---------------------------------
                for att in range(1, MAX_RETRY + 1):
                    try:
                        resp = requests.get(full, timeout=10)
                        resp.raise_for_status()
                        break
                    except requests.RequestException as e:
                        if att == MAX_RETRY:
                            print(f"❌ HTTP 실패: {bill_id} p{page}")
                            failed_bills.append(bill_id)
                            return saved_total
                        time.sleep(1)

                # ---- XML 파싱 ------------------------------------
                try:
                    root = ET.fromstring(resp.text)
                except ET.ParseError as e:
                    print(f"❌ XML 파싱 실패: {bill_id} p{page} {e}")
                    failed_bills.append(bill_id)
                    break

                rows = root.findall(".//row") or root.findall(".//{*}row")
                if not rows:
                    break

                # ---- 표결 행 처리 --------------------------------
                for row in rows:
                    mona   = tag(row, "MONA_CD")
                    result = tag(row, "RESULT_VOTE_MOD", "RESULT_VOTE", "RST_VOTE")
                    if not (mona and result):
                        continue
                    if mona in existing:
                        continue

                    member = member_map.get(mona)
                    if not member:
                        missing_mem[mona] += 1
                        continue

                    buf.append(Vote(bill=bill, member=member, vote_result=result))
                    existing.add(mona)

                    if len(buf) >= BATCH_SIZE:
                        saved_total = flush_votes(buf, saved_total)
                        buf.clear()

                if len(rows) < P_SIZE:
                    break
                page += 1
                time.sleep(CONCURRENCY_PS)

    # ---- 잔여 버퍼 저장 ------------------------------------------
    if buf:
        saved_total = flush_votes(buf, saved_total)

    # ---- 요약 출력 ------------------------------------------------
    print(f"\n🎉 최종 저장된 표결 수: {saved_total:,}")
    if failed_bills:
        print(f"⚠️ 실패 Bill {len(set(failed_bills))}건: {failed_bills[:10]} …")
    if missing_mem:
        miss_top = sorted(missing_mem.items(), key=lambda x: -x[1])[:10]
        print(f"⚠️ DB에 없는 의원 {len(missing_mem)}명 중 상위 10: {miss_top}")
    return saved_total
