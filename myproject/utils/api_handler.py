import requests
from decouple import config
from api.models import Bill,PartyDistribution
import xml.etree.ElementTree as ET
import re


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


def extract_sido(location: str) -> str:
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

    # 키 중 하나가 location에 포함되어 있으면 매핑값 반환
    for key, val in mapping.items():
        if key in location:
            return val

    # 그 외
    return '기타'


def get_party_distribution_by_daesu(daesu):
    bills = Bill.objects.filter(daesu=daesu)  # daesu에 맞는 법안 가져오기
    
    region_party_count = {}
    total_counts = {}  # 각 지역구의 총 후보자 수

    # 각 법안에 대해 지역구와 정당 정보 처리
    for bill in bills:
        region = bill.electionDistrict.strip()  # 지역구
        parties = bill.proposerParty.strip()    # 정당
        print("▶ 원본 region:", repr(region))
        
        if not region or not parties:
            continue

        # 비례대표 따로 처리
        if "비례대표" in region:
            region_key = "비례대표"
        else:
            region_key = extract_sido(region)  # 시·도 단위 추출
            print("   → 추출된 region_key:", repr(region_key))

        # 정당이 여러 개인 경우 쉼표 기준으로 분리
        for party in parties.split(','):
            party = party.strip()
            if not party:
                continue

            # 지역구와 정당 정보를 딕셔너리에 통합
            if region_key not in region_party_count:
                region_party_count[region_key] = {}

            region_party_count[region_key][party] = region_party_count[region_key].get(party, 0) + 1

            # 총 후보자 수 집계
            if region_key not in total_counts:
                total_counts[region_key] = 0
            total_counts[region_key] += 1

    # 통합된 결과 출력 (확인용)
    integrated_region_party_count = {}

    # 지역별로 정당 수치를 통합
    for region, party_counts in region_party_count.items():
        if region not in integrated_region_party_count:
            integrated_region_party_count[region] = {}

        for party, count in party_counts.items():
            integrated_region_party_count[region][party] = integrated_region_party_count[region].get(party, 0) + count

    # 결과를 PartyDistribution 모델에 저장
    for region, party_counts in integrated_region_party_count.items():
        total_count = total_counts.get(region, 0)
        
        for party, count in party_counts.items():
            # 새로운 PartyDistribution 객체 생성
            distribution = PartyDistribution.objects.create(
                daesu=daesu,  # 여기서 대수를 넣어줍니다.
                region=region,
                party=party,
                count=count
            )
            # 비율 계산 후 저장
            distribution.calculate_percentage(total_count)
            distribution.save()

    # 결과 출력 (확인용)
    for region, party_counts in integrated_region_party_count.items():
        print(f"[{region}]")
        for party, count in party_counts.items():
            print(f"  {party}: {count}")

    return integrated_region_party_count


