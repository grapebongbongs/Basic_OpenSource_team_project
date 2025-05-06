import requests
from decouple import config
from api.models import Bill,PartyDistribution, Representative
import xml.etree.ElementTree as ET
import re
from django.shortcuts import render
from bs4 import BeautifulSoup

def test_api():
    """
    국회 API에서 모든 페이지의 데이터를 반복적으로 호출하여 수집.
    """
    URL = "https://open.assembly.go.kr/portal/openapi/ALLSCHEDULE"
    all_rows = []
    page = 1
    page_size = 1000

    while True:
        params = {
            "KEY": config("ASSEMBLY_API_KEY"),
            "Type": "json",
            "pIndex": page,
            "pSize": page_size
        }

        resp = requests.get(URL, params=params)
        try:
            data = resp.json()
        except ValueError:
            print(f"[test_api] 페이지 {page} JSON 파싱 실패:", resp.text)
            break

        if not isinstance(data, dict) or 'ALLSCHEDULE' not in data:
            print(f"[test_api] 페이지 {page}에서 예기치 않은 응답 구조:", data)
            break

        schedule_list = data.get('ALLSCHEDULE')
        if not isinstance(schedule_list, list) or len(schedule_list) < 2:
            print(f"[test_api] 페이지 {page}에서 'ALLSCHEDULE' 구조 이상")
            break

        row_data = schedule_list[1].get('row', [])
        if isinstance(row_data, dict):
            row_data = [row_data]

        if not row_data:
            print(f"[test_api] 페이지 {page}에 더 이상 데이터 없음. 종료.")
            break

        all_rows.extend(row_data)
        print(f"[test_api] 페이지 {page}에서 {len(row_data)}건 수집됨.")
        page += 1

    print(f"[test_api] 총 수집된 데이터 개수: {len(all_rows)}")
    return all_rows


def save_bills_to_db():
    """
    test_api()로 가져온 모든 데이터를 DB에 저장합니다.
    """
    rows = test_api()
    if not rows:
        print("[save_bills_to_db] 저장할 데이터가 없습니다.")
        return

    created_count = 0
    for item in rows:
        obj, created = Bill.objects.get_or_create(
            SCH_KIND=item.get('SCH_KIND', ''),
            SCH_CN=item.get('SCH_CN', ''),
            SCH_DT=item.get('SCH_DT', ''),
            SCH_TM=item.get('SCH_TM', '') or '',
            CONF_DIV=item.get('CONF_DIV', '') or '',
            CMIT_NM=item.get('CMIT_NM', '') or '',
            CONF_SESS=item.get('CONF_SESS', '') or '',
            CONF_DGR=item.get('CONF_DGR', '') or '',
            EV_INST_NM=item.get('EV_INST_NM', '') or '',
            EV_PLC=item.get('EV_PLC', '') or ''
        )
        if created:
            created_count += 1

    print(f"[save_bills_to_db] 총 {len(rows)}건 중 {created_count}건이 새로 저장되었습니다.")

def extract_sido(location: str) :
    """
    전체 지역명(예: '서귀포시', '제주시', '경기도 수원시무')에서
    SVG data-region 값(시·도 단위)인 '제주', '경기' 등으로 매핑합니다.
    """
    # 시·군·구 → 시·도 매핑 테이블
    mapping = {
        # 광역시·도
        '서울': '서울', '부산': '부산', '대구': '대구', '인천': '인천',
        '광주': '광주', '대전': '대전', '울산': '울산', '세종': '세종',
        '경기도': '경기', '경기': '경기',
        '강원도': '강원', '강원': '강원',
        '충청북도': '충북', '충북': '충북',
        '충청남도': '충남', '충남': '충남',
        '전라북도': '전북', '전북': '전북',
        '전라남도': '전남', '전남': '전남',
        '경상북도': '경북', '경북': '경북',
        '경상남도': '경남', '경남': '경남',
        '제주특별자치도': '제주', '제주도': '제주', '제주': '제주',
        # 제주 하위 시
        '서귀포시': '제주', '제주시': '제주',
        }
    for key, val in mapping.items():
        if key in location:
            return val

    # 그 외
    return '기타'



def load_distribution_to_db(daesu: int):
    API_URL = "https://open.assembly.go.kr/portal/openapi/nprlapfmaufmqytet"
    params = {
        "KEY": config("ASSEMBLY_API_KEY"),
        "Type": "xml",
        "pIndex": 1,
        "pSize": 300,
        "DAESU": str(daesu),
    }
    resp = requests.get(API_URL, params=params)
    resp.raise_for_status()

    # BeautifulSoup을 이용한 XML 파싱 (불량 문자 방지)
    soup = BeautifulSoup(resp.content, 'lxml-xml')

    pattern = re.compile(
        rf"제{daesu}대국회의원\((?P<region>[^)]+)\)\s*"
        r"(?P<party>[^제]+?)(?=(?:제\d+대국회의원|$))"
    )

    raw_count = {}
    total_count = {}

    rows = soup.find_all("row")
    for row in rows:
        text_tag = row.find("DAE")
        text = text_tag.text.strip() if text_tag and text_tag.text else ""

        print(f"텍스트: {text}")

        for m in pattern.finditer(text):
            full_region = m.group("region").strip()
            party = m.group("party").strip()

            print(f"전체 지역: {full_region}, 정당: {party}")

            if "비례대표" in full_region:
                sido = "비례대표"
            else:
                sido = extract_sido(full_region)

            print(f"시·도: {sido}")

            raw_count.setdefault(sido, {})
            raw_count[sido][party] = raw_count[sido].get(party, 0) + 1
            total_count[sido] = total_count.get(sido, 0) + 1

    print(f"raw_count: {raw_count}")
    print(f"total_count: {total_count}")

    # 기존 데이터 삭제
    PartyDistribution.objects.filter(daesu=daesu).delete()

    # 저장
    for region, parties in raw_count.items():
        tot = total_count.get(region, 0)
        for party, cnt in parties.items():
            PartyDistribution.objects.create(
                daesu=daesu,
                region=region,
                party=party,
                count=cnt,
                percentage=(cnt / tot * 100) if tot else 0,
            )

def normalize_party_name(party: str) -> str:
    """정당 이름 정규화"""
    return party.replace("·", "·").replace(".", "·").replace("ㆍ", "·").strip()

def load_representatives_to_db(daesu: int):
    API_URL = "https://open.assembly.go.kr/portal/openapi/nprlapfmaufmqytet"
    params = {
        "KEY": config("ASSEMBLY_API_KEY"),
        "Type": "xml",
        "pIndex": 1,
        "pSize": 300,
        "DAESU": str(daesu),
    }
    resp = requests.get(API_URL, params=params)
    resp.raise_for_status()

    # lxml을 사용하여 XML을 파싱
    soup = BeautifulSoup(resp.content, 'lxml-xml')

    # 기존 레코드 삭제 (갱신)
    Representative.objects.filter(year=daesu).delete()

    # 예: "제21대국회의원(경남 창원시성산구) 새누리당"
    rep_pattern = re.compile(
        rf"제{daesu}대국회의원\((?P<region>[^)]+)\)\s*(?P<party>[^제]+)"
    )

    for row in soup.find_all("row"):
        name = row.find("NAME").text.strip()
        dae = row.find("DAE").text.strip()
        m = rep_pattern.search(dae)
        if not (name and m):
            continue

        full_region = m.group("region").strip()
        party = normalize_party_name(m.group("party").strip())

        # 시·도 키 결정
        if "비례대표" in full_region:
            region_key = "비례대표"
        else:
            region_key = extract_sido(full_region)

        Representative.objects.create(
            name=name,
            party=party,
            region=region_key,
            year=daesu,
        )