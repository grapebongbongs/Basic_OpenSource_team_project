
import re
import requests
import xml.etree.ElementTree as ET

from django.shortcuts import render
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse


from rest_framework.decorators import api_view
from rest_framework.response import Response

from decouple import config
from .models import Bill, PartyDistribution,Representative
from utils.api_handler import load_distribution_to_db, load_representatives_to_db

# ------------------------------------------------------------------
# 1) 기존 Bill / Calendar / Search 뷰 (변경 없음)
# ------------------------------------------------------------------

def calendar_page(request):
    """
    캘린더 페이지를 렌더링합니다.
    """
    return render(request, 'calendar/calendar.html')

def calendar_events(request):
    start = request.GET.get('start')
    end = request.GET.get('end')

    print(f"Start: {start}, End: {end}")  # start와 end 값 출력

    qs = Bill.objects.all()
    if start and end:
        qs = qs.filter(SCH_DT__gte=start, SCH_DT__lte=end)
    
    print(f"Filtered events count: {qs.count()}")  # 필터링된 결과 수 출력

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


def party_map_view(request):
    daesu = int(request.GET.get('daesu', 21))  # 기본값: 21대

    # 초기 요청 시점에 해당 대수의 데이터만 로드
<<<<<<< HEAD
    if not Representative.objects.filter(daesu=daesu).exists():
=======
    if not Representative.objects.filter(year=daesu).exists():
>>>>>>> 67ada50ee672eb98107cd90b9a41e6a0a5bc157d
        load_representatives_to_db(daesu)
    if not PartyDistribution.objects.filter(daesu=daesu).exists():
        load_distribution_to_db(daesu)

    return render(request, 'map/map.html', {'daesu': daesu})

# -----------------------------------------------------------
# 정당 분포 데이터 API
# -----------------------------------------------------------

@api_view(['GET'])

def party_data_api(request):
    daesu = request.GET.get('daesu')
    if not daesu:
        return Response({"error": "daesu parameter is required"}, status=400)
    
    daesu = int(daesu)  # daesu 값을 정수로 변환

    # DB에 데이터가 없으면 외부 API에서 로드
    if not PartyDistribution.objects.filter(daesu=daesu).exists():
        load_distribution_to_db(daesu)

    # PartyDistribution 모델에서 데이터를 가져오기
    qs = PartyDistribution.objects.filter(daesu=daesu)
    result = {}
    for pd in qs:
        result.setdefault(pd.region, []).append({
            "party": pd.party,
            "percentage": round(pd.percentage, 1)
        })

    return JsonResponse(result)


# -----------------------------------------------------------
# 의원 데이터 API
# -----------------------------------------------------------
@api_view(['GET'])
def representative_data_api(request):
    daesu = request.GET.get('daesu')
<<<<<<< HEAD
    region = request.GET.get('region')  # 시도명 또는 "비례대표" 가능

    if not daesu:
        return Response({"error": "daesu parameter is required"}, status=400)

    try:
        daesu = int(daesu)
    except ValueError:
        return Response({"error": "daesu must be an integer"}, status=400)

    # DB에 데이터가 없으면 외부 API에서 로드
    if not Representative.objects.filter(daesu=daesu).exists():
        print(f"[DEBUG] Loading representatives for {daesu}대")
        load_representatives_to_db(daesu)

    # 쿼리셋 생성
    qs = Representative.objects.filter(daesu=daesu)

=======
    region = request.GET.get('region')  # 지역도 함께 받음
    if not daesu:
        return Response({"error": "daesu parameter is required"}, status=400)

    daesu = int(daesu)  # daesu 값을 정수로 변환

    # DB에 데이터가 없으면 외부 API에서 로드
    if not Representative.objects.filter(year=daesu).exists():
        print(f"[DEBUG] Loading representatives for {daesu}대")
        load_representatives_to_db(daesu)

    # Representative 모델에서 데이터를 가져오기
    qs = Representative.objects.filter(year=daesu)

    # region이 요청되었을 경우 해당 지역만 필터링
>>>>>>> 67ada50ee672eb98107cd90b9a41e6a0a5bc157d
    if region:
        print(f"[DEBUG] Filtering by region: {region}")
        qs = qs.filter(region=region)

    print(f"[DEBUG] Representatives count: {qs.count()}")

<<<<<<< HEAD
    # 지역별 데이터 구성
=======
>>>>>>> 67ada50ee672eb98107cd90b9a41e6a0a5bc157d
    data = {}
    for rep in qs:
        data.setdefault(rep.region, []).append({
            "name": rep.name,
            "party": rep.party
        })

<<<<<<< HEAD
    return JsonResponse(data)
=======
    return JsonResponse(data)
>>>>>>> 67ada50ee672eb98107cd90b9a41e6a0a5bc157d
