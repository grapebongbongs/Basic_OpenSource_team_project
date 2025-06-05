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


# 정당 이름 정규화 매핑 테이블
PARTY_NAME_MAP = {
    '평민당': '평화민주당',
    '민정당': '민주정의당',
    '국민회의' : '새정치국민회의',
    '민주' : '민주당',
    '민자당': '민주자유당',
    '국민당' : '통일국민당',
}

def normalize_party_name(party: str) -> str:
    party = (
        party.replace("ㆍ", "·")  # 유사한 특수문자 통일
             .replace("·", "·")     # 점 문자 통일 (필요 시 유지)
             .replace(".", "·")      # 마침표(.)를 중점으로 통일
             .replace(" ", "")       # 불필요한 공백 제거
             .strip()
    )
    return PARTY_NAME_MAP.get(party, party)

def extract_sido(location: str):
    mapping = {
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
        '서귀포시': '제주', '제주시': '제주',
    }
    for key, val in mapping.items():
        if key in location:
            return val
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

    soup = BeautifulSoup(resp.content, 'lxml-xml')

    pattern = re.compile(
        rf"제{daesu}대국회의원\((?P<region>[^)]+)\)\s*(?P<party>[^제]+?)(?=(?:제\d+대국회의원|$))"
    )

    raw_count = {}
    total_count = {}

    rows = soup.find_all("row")
    for row in rows:
        text_tag = row.find("DAE")
        text = text_tag.text.strip() if text_tag and text_tag.text else ""

        for m in pattern.finditer(text):
            full_region = m.group("region").strip()
            party = normalize_party_name(m.group("party").strip())

            sido = "비례대표" if "비례대표" in full_region else extract_sido(full_region)

            raw_count.setdefault(sido, {})
            raw_count[sido][party] = raw_count[sido].get(party, 0) + 1
            total_count[sido] = total_count.get(sido, 0) + 1

    PartyDistribution.objects.filter(daesu=daesu).delete()
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
<<<<<<< HEAD
=======

>>>>>>> 67ada50ee672eb98107cd90b9a41e6a0a5bc157d
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

    soup = BeautifulSoup(resp.content, 'lxml-xml')
<<<<<<< HEAD
    # year → daesu 로 수정
    Representative.objects.filter(daesu=daesu).delete()
=======
    Representative.objects.filter(year=daesu).delete()
>>>>>>> 67ada50ee672eb98107cd90b9a41e6a0a5bc157d

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

        region_key = "비례대표" if "비례대표" in full_region else extract_sido(full_region)

<<<<<<< HEAD
        # year → daesu 로 수정
=======
>>>>>>> 67ada50ee672eb98107cd90b9a41e6a0a5bc157d
        Representative.objects.create(
            name=name,
            party=party,
            region=region_key,
<<<<<<< HEAD
            daesu=daesu,
=======
            year=daesu,
>>>>>>> 67ada50ee672eb98107cd90b9a41e6a0a5bc157d
        )
