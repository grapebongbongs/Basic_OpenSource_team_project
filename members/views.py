from django.shortcuts import render, get_object_or_404, redirect
from .models import AssemblyMember
from utils.members_handler import fetch_and_store_current_members
from django.db.models import Q

def update_and_show_main(request):
    fetch_and_store_current_members()


    unit_cd = request.GET.get('unit_cd')
    query = request.GET.get('q', '').strip()  #query를 받아옴


    if unit_cd == '100022':
        base_qs = AssemblyMember.objects.filter(Q(unit_cd='100022') | (Q(phone__isnull=False) & ~Q(phone='')))
    elif unit_cd:
        base_qs = AssemblyMember.objects.filter(unit_cd=unit_cd)
    else:
        base_qs = AssemblyMember.objects.all()


    # 검색어가 있을 경우 name, origin, party에 대해 OR 검색
    if query:
        base_qs = base_qs.filter(
            Q(name__iexact=query) |          # 이름: 정확히 일치 (대소문자 무시)
            Q(origin__icontains=query) |     # 출신지: 포함 검색
            Q(party__iexact=query)           # 정당: 정확히 일치 (대소문자 무시)
        )

    # 이름 기준 정렬
    members = base_qs.order_by('name')

    # 최종 데이터 구조 생성
    modified_members = []
    for member in members:
        c = member.committee
        if member.committee and "," in member.committee:
            c = member.committee.split(",")[0] + " 등"


        modified_members.append({
            "name": member.name,
            "committee": c,
            "party": member.party,
            "image_url": member.image_url,
            "origin": member.origin,
            "mona_cd": member.mona_cd,

        })
    return render(request, 'main/main.html', {'members': modified_members})


def redirect_to_vote(request, mona_cd):
    """
    mona_cd를 추출하여 vote 앱으로 리다이렉트하는 함수
    """
    # 유효한 `mona_cd`인지 확인
    member = get_object_or_404(AssemblyMember, mona_cd=mona_cd)
    
    # vote 앱의 member_detail 뷰로 리다이렉트
    return redirect('vote:member_detail', mona_cd=mona_cd)


