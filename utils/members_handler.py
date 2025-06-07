"""
assembly_sync_debug.py
────────────────────────────────
20·21대 의원 동기화 + 핵심 디버그 스텝 포함
────────────────────────────────
"""
import os, time, json, requests, xml.etree.ElementTree as ET
from django.conf import settings
from django.db import transaction
from members.models import AssemblyMember

SESSION = requests.Session()
SESSION.headers.update({'User-Agent': 'assembly-sync/1.0 (+https://yourdomain)'})
API_KEY = settings.ASSEMBLY_API_KEY

# ──────────────────────────────
def _xml_rows(url: str, params: dict, max_retry=3):
    params = {'KEY': API_KEY, 'type': 'xml', **params}
    for attempt in range(1, max_retry + 1):
        try:
            r = SESSION.get(url, params=params, timeout=10)
            r.raise_for_status()
            root = ET.fromstring(r.text)
            return root.findall('row')
        except Exception as err:
            print(f"⏳  RETRY {attempt}/{max_retry} ({url}?pIndex={params.get('pIndex')}) → {err}")
            time.sleep(attempt * 2)
    return []

# ──────────────────────────────
def fetch_and_store_current_members():
    url = 'https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu'
    p_idx, created, api_mona_codes = 1, 0, set()

    while True:
        rows = _xml_rows(url, {'pIndex': p_idx, 'pSize': 100})
        # ── DEBUG: page별 row 개수·의원 이름 확인
        print(f"📥  CURRENT pIndex={p_idx} → rows={len(rows)} {'('+rows[0].findtext('HG_NM')+')' if rows else ''}")

        if not rows:
            break
        bulk = []
        for row in rows:
            mona_cd = row.findtext('MONA_CD')
            if not mona_cd:
                continue
            api_mona_codes.add(mona_cd)
            if AssemblyMember.objects.filter(mona_cd=mona_cd).exists():
                continue
            bulk.append(AssemblyMember(
                mona_cd=mona_cd,
                name=row.findtext('HG_NM') or '',
                hj_nm=row.findtext('HJ_NM') or '',
                party=row.findtext('POLY_NM') or '',
                committee=row.findtext('CMIT_NM') or '',
                position=row.findtext('JOB_RES_NM') or '',
                elect_gbn=row.findtext('ELECT_GBN_NM') or '',
                origin=row.findtext('ORIG_NM') or '',
                email=row.findtext('E_MAIL') or '',
                phone=row.findtext('TEL_NO') or '',
                homepage=row.findtext('HOMEPAGE') or '',
                unit=row.findtext('UNITS') or '',
                title=row.findtext('MEM_TITLE') or '',
                staff=row.findtext('STAFF') or '',
                secretary=row.findtext('SECRETARY') or '',
                assem_addr=row.findtext('ASSEM_ADDR') or '',
            ))
        AssemblyMember.objects.bulk_create(bulk)
        created += len(bulk)
        p_idx += 1

    # ── DEBUG: API↔DB 불일치 목록 출력
    db_codes = set(AssemblyMember.objects.values_list('mona_cd', flat=True))
    missing = api_mona_codes - db_codes
    print(f"🔍  API에는 있는데 DB에 없는 mona_cd = {sorted(missing)[:10]} ... 총 {len(missing)}명")

    print(f"🆕  신규 의원 {created}명 저장")
    return created

# ──────────────────────────────
def patch_unit_cd(unit_cds=(100020, 100021, 100022)):
    url = 'https://open.assembly.go.kr/portal/openapi/npffdutiapkzbfyvr'
    updated, created = 0, 0

    codes_to_remove = {'100019'}
    for m in AssemblyMember.objects.exclude(unit_cd__isnull=True).iterator():
        units = set(filter(None, m.unit_cd.split(',')))
        new_units = units - codes_to_remove
        if units != new_units:
            m.unit_cd = ','.join(sorted(new_units)) or None   # 전부 지워지면 NULL
            m.save(update_fields=['unit_cd'])


    for unit_cd in unit_cds:
        p_idx = 1
        while True:
            rows = _xml_rows(url, {'UNIT_CD': unit_cd, 'pIndex': p_idx, 'pSize': 100})
            print(f"📥  UNIT {unit_cd} pIndex={p_idx} rows={len(rows)}")  # ── DEBUG
            if not rows:
                break
            for row in rows:
                mona_cd = row.findtext('MONA_CD')
                if not mona_cd:
                    continue
                member = AssemblyMember.objects.filter(mona_cd=mona_cd).first()
                if member:
                    units = [u for u in (member.unit_cd or '').split(',') if u]
                    if str(unit_cd) not in units:
                        units.append(str(unit_cd))
                        member.unit_cd = ','.join(sorted(units))
                        member.save(update_fields=['unit_cd'])
                        updated += 1
                else:
                    AssemblyMember.objects.create(
                        mona_cd=mona_cd,
                        name=row.findtext('HG_NM') or '',
                        hj_nm=row.findtext('HJ_NM') or '',
                        unit=row.findtext('UNITS') or '',
                        unit_cd=str(unit_cd),
                        origin=row.findtext('ORIG_NM') or '',
                        elect_gbn=row.findtext('ELECT_GBN_NM') or '',
                        party=row.findtext('POLY_NM') or ''
                    )
                    created += 1
            p_idx += 1
    print(f"🔁  UNIT_CD 누적: 기존 {updated} / 신규 {created}")
    return updated + created

# ──────────────────────────────
def patch_member_images():
    url = 'https://open.assembly.go.kr/portal/openapi/ALLNAMEMBER'
    p_idx, patched = 1, 0
    while True:
        rows = _xml_rows(url, {'pIndex': p_idx, 'pSize': 100})
        print(f"📥  IMAGES pIndex={p_idx} rows={len(rows)}")  # ── DEBUG
        if not rows:
            break
        for row in rows:
            mona_cd = row.findtext('NAAS_CD')
            if not mona_cd:
                continue
            try:
                m = AssemblyMember.objects.get(mona_cd=mona_cd)
            except AssemblyMember.DoesNotExist:
                continue
            img, cmte = row.findtext('NAAS_PIC') or '', row.findtext('CMIT_NM') or ''
            if (img and not m.image_url) or (cmte and not m.committee):
                if img and not m.image_url:
                    m.image_url = img
                if cmte and not m.committee:
                    m.committee = cmte
                m.save(update_fields=['image_url', 'committee'])
                patched += 1
        p_idx += 1
    print(f"🖼️  사진·위원회 업데이트: {patched}")
    return patched

# ──────────────────────────────
@transaction.atomic
def fetch_all_members_and_images():
    print("🚀  의원 기본 정보 동기화 시작")
    new_cnt = fetch_and_store_current_members()
    unit_cnt = patch_unit_cd(unit_cds=[100020, 100021, 100022])  # 필요 시 확장
    img_cnt  = patch_member_images()
    summary = {'new': new_cnt, 'unit_cd': unit_cnt, 'images': img_cnt}
    print("✅  최종 결과:", json.dumps(summary, ensure_ascii=False, indent=2))
    return summary