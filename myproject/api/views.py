
import re
import requests
import xml.etree.ElementTree as ET

from django.shortcuts import render
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework.decorators import api_view
from rest_framework.response import Response

from decouple import config
from .models import Bill, PartyDistribution,Representative

# ------------------------------------------------------------------
# 1) 기존 Bill / Calendar / Search 뷰 (변경 없음)
# ------------------------------------------------------------------

def calendar_page(request):
    """
    캘린더 페이지를 렌더링합니다.
    """
    return render(request, 'api/calendar.html')


def calendar_events(request):
    """
    FullCalendar 이벤트 리스트(JSON) 반환
    """
    start = request.GET.get('start')
    end   = request.GET.get('end')

    qs = Bill.objects.all()
    if start and end:
        qs = qs.filter(SCH_DT__gte=start, SCH_DT__lte=end)

    events = []
    for b in qs:
        date = b.SCH_DT
        time = (b.SCH_TM or '').strip()

        if '~' in time:
            start_iso = f"{date}T{time.split('~')[0]}"
        elif time:
            start_iso = f"{date}T{time}"
        else:
            start_iso = date

        events.append({
            'title': b.SCH_CN,
            'start': start_iso,
            'allDay': False,
            'extendedProps': {
                'kind': b.SCH_KIND,
                'committee': b.CMIT_NM,
                'place': b.EV_PLC,
            }
        })

    return JsonResponse(events, safe=False)


def search_page(request):
    """
    검색 UI 페이지 렌더링
    """
    query = request.GET.get('q', '')
    page_num = request.GET.get('page', 1)

    if query:
        qs = Bill.objects.filter(
            Q(SCH_KIND__icontains=query) |
            Q(SCH_CN__icontains=query) |
            Q(CMIT_NM__icontains=query) |
            Q(EV_INST_NM__icontains=query) |
            Q(EV_PLC__icontains=query)
        )
    else:
        qs = Bill.objects.none()

    paginator = Paginator(qs, 20)
    try:
        results = paginator.page(page_num)
    except PageNotAnInteger:
        results = paginator.page(1)
    except EmptyPage:
        results = paginator.page(paginator.num_pages)

    return render(request, 'api/search.html', {
        'query': query,
        'results': results,
        'paginator': paginator,
    })


@api_view(['GET'])
def search_bills(request):
    """
    REST API: 최대 20건 검색 결과 JSON
    """
    query = request.GET.get('q', '')
    bills = Bill.objects.filter(
        Q(SCH_KIND__icontains=query) |
        Q(SCH_CN__icontains=query) |
        Q(CMIT_NM__icontains=query) |
        Q(EV_INST_NM__icontains=query) |
        Q(EV_PLC__icontains=query)
    )[:20]

    results = [{
        "SCH_KIND": b.SCH_KIND,
        "SCH_CN":   b.SCH_CN,
        "SCH_DT":   b.SCH_DT,
        "SCH_TM":   b.SCH_TM,
        "CONF_DIV": b.CONF_DIV,
        "CMIT_NM":  b.CMIT_NM,
        "CONF_SESS":b.CONF_SESS,
        "CONF_DGR": b.CONF_DGR,
        "EV_INST_NM": b.EV_INST_NM,
        "EV_PLC":     b.EV_PLC,
    } for b in bills]

    return Response({"data": results})


def extract_sido(location: str) -> str:
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
        '제주특별자치도': '제주', '제주도': '제주',
        '서귀포시': '제주', '제주시': '제주',
    }
    for key, val in mapping.items():
        if key in location:
            return val
    return '기타'


# —————————————————————————————————————
# 2) 외부 API 파싱 + PartyDistribution 저장
# —————————————————————————————————————
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

    root = ET.fromstring(resp.content)

    # “제{daesu}대국회의원(지역) 정당” 패턴
    pattern = re.compile(
        rf"제{daesu}대국회의원\((?P<region>[^)]+)\)\s*"
        r"(?P<party>[^제]+?)(?=(?:제\d+대국회의원|$))"
    )

    raw_count = {}
    total_count = {}

    for row in root.iter("row"):
        text = row.findtext("DAE", "")
        for m in pattern.finditer(text):
            full_region = m.group("region").strip()
            party = m.group("party").strip()

            # 시·도 키 결정
            if "비례대표" in full_region:
                sido = "비례대표"
            else:
                sido = extract_sido(full_region)

            # 후보 수 집계
            raw_count.setdefault(sido, {})
            raw_count[sido][party] = raw_count[sido].get(party, 0) + 1
            total_count[sido] = total_count.get(sido, 0) + 1

    # 기존 레코드 삭제(갱신)
    PartyDistribution.objects.filter(daesu=daesu).delete()

    # DB 저장
    for region, parties in raw_count.items():
        tot = total_count.get(region, 0)
        for party, cnt in parties.items():
            dist = PartyDistribution(
                daesu=daesu,
                region=region,
                party=party,
                count=cnt,
                percentage=(cnt / tot * 100) if tot else 0,
            )
            dist.save()


# —————————————————————————————————————
# 3) 외부 API 파싱 + Representative 저장
# —————————————————————————————————————
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

    root = ET.fromstring(resp.content)

    # 기존 레코드 삭제(갱신)
    Representative.objects.filter(year=daesu).delete()

    # XML에는 NAME, DAE, DAE 필드만 있으니 region/party는 DAE 문자열에서 파싱
    # 예: DAE="제21대국회의원(경남 창원시성산구) 새누리당"
    rep_pattern = re.compile(
        rf"제{daesu}대국회의원\((?P<region>[^)]+)\)\s*(?P<party>[^제]+)"
    )

    for row in root.iter("row"):
        name = row.findtext("NAME", "").strip()
        dae = row.findtext("DAE", "")
        m = rep_pattern.search(dae)
        if not (name and m):
            continue
        full_region = m.group("region").strip()
        party = m.group("party").strip()

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


# —————————————————————————————————————
# 4) 지도 페이지 렌더링
# —————————————————————————————————————
def party_map_view(request):
    daesu = int(request.GET.get('daesu', 21))
    return render(request, 'map.html', {'daesu': daesu})


# —————————————————————————————————————
# 5) 분포 데이터 API
# —————————————————————————————————————
@api_view(['GET'])
@csrf_exempt
def party_data_api(request):
    daesu = request.GET.get('daesu')
    if not daesu:
        return Response({"error": "daesu parameter is required"}, status=400)
    daesu = int(daesu)

    # DB에 데이터가 없으면 외부 API에서 로드
    if not PartyDistribution.objects.filter(daesu=daesu).exists():
        load_distribution_to_db(daesu)

    qs = PartyDistribution.objects.filter(daesu=daesu)
    result = {}
    for pd in qs:
        result.setdefault(pd.region, []).append({
            "party": pd.party,
            "percentage": round(pd.percentage, 1)
        })

    return JsonResponse(result)


# —————————————————————————————————————
# 6) 의원 정보 API
# —————————————————————————————————————
@api_view(['GET'])
@csrf_exempt
def representative_data_api(request):
    daesu = request.GET.get('daesu')
    if not daesu:
        return Response({"error": "daesu parameter is required"}, status=400)
    daesu = int(daesu)

    # DB에 데이터가 없으면 외부 API에서 로드
    if not Representative.objects.filter(year=daesu).exists():
        load_representatives_to_db(daesu)

    qs = Representative.objects.filter(year=daesu)
    data = {}
    for rep in qs:
        data.setdefault(rep.region, []).append({
            "name": rep.name,
            "party": rep.party
        })

    return JsonResponse(data)