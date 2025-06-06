from django.shortcuts import render, get_object_or_404, redirect
from .models import AssemblyMember
from utils.members_handler import fetch_and_store_current_members
from django.db.models import Q
from django.core.paginator import Paginator

def update_and_show_main(request):
    fetch_and_store_current_members()

    unit_cd = request.GET.get('unit_cd')
    query = request.GET.get('q', '').strip()

    if unit_cd == '100022':
        base_qs = AssemblyMember.objects.filter(Q(unit_cd='100022') | (Q(phone__isnull=False) & ~Q(phone='')))
    elif unit_cd:
        base_qs = AssemblyMember.objects.filter(unit_cd__contains=unit_cd)
    else:
        base_qs = AssemblyMember.objects.all()

    if query:
        base_qs = base_qs.filter(
            Q(name__iexact=query) |
            Q(origin__icontains=query) |
            Q(party__iexact=query)
        )

    members = base_qs.order_by('name')

    # 페이지네이션
    paginator = Paginator(members, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # 페이지 그룹 계산
    total_pages = paginator.num_pages
    group_size = 10
    current_group = (page_obj.number - 1) // group_size
    start_page = current_group * group_size + 1
    end_page = min(start_page + group_size - 1, total_pages)
    custom_page_range = range(start_page, end_page + 1)

    # ✅ object_list 기반으로 수정된 리스트 생성
    modified_members = []
    for member in page_obj.object_list:
        committee_str = member.committee
        if committee_str and "," in committee_str:
            committee_str = committee_str.split(",")[0] + " 등"

        modified_members.append({
            "name": member.name,
            "committee": committee_str,
            "party": member.party,
            "image_url": member.image_url,
            "origin": member.origin,
            "mona_cd": member.mona_cd,
        })

    # ✅ page_obj를 템플릿에 넘기되, members 대신 page_obj 사용
    page_obj.object_list = modified_members  # 핵심!

    return render(request, 'main/main.html', {
        'members': page_obj,
        'custom_page_range': custom_page_range,
        'has_previous_group': start_page > 1,
        'has_next_group': end_page < total_pages,
        'previous_group_page': start_page - 1,
        'next_group_page': end_page + 1,
        'request': request  # ✅ 꼭 넣어줘야 함
    })


def redirect_to_vote(request, mona_cd):
    """
    mona_cd를 추출하여 vote 앱으로 리다이렉트하는 함수
    """
    # 유효한 `mona_cd`인지 확인
    member = get_object_or_404(AssemblyMember, mona_cd=mona_cd)
    
    # vote 앱의 member_detail 뷰로 리다이렉트
    return redirect('vote:member_detail', mona_cd=mona_cd)


