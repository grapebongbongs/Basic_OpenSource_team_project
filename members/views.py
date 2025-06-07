from django.shortcuts import render, get_object_or_404, redirect
from .models import AssemblyMember
from utils.members_handler import fetch_and_store_current_members
from django.db.models import Q
from django.core.paginator import Paginator


def update_and_show_main(request):
    fetch_and_store_current_members()

    unit_cd = request.GET.get('unit_cd')
    query   = request.GET.get('q', '').strip()
    dist    = request.GET.get('dist', '').strip()

    # 기본 queryset
    base_qs = AssemblyMember.objects.all()

    # ⭐ 1) unit_cd 우선 적용 -------------------------------------------------
    if unit_cd:
        if unit_cd == '100022':
            base_qs = base_qs.filter(
                Q(unit_cd='100022') |
                (Q(phone__isnull=False) & ~Q(phone=''))
            )
        else:
            base_qs = base_qs.filter(unit_cd__contains=unit_cd)

    # ⭐ 2) dist(지역) 필터 --------------------------------------------------
    if dist:
        base_qs = base_qs.filter(origin__icontains=dist)

    # ⭐ 3) 검색어(q) 필터 ---------------------------------------------------
    if query:
        base_qs = base_qs.filter(
            Q(name__iexact=query)   |
            Q(origin__icontains=query) |
            Q(party__iexact=query)
        )

    # ----------------------------------------------------------------------
    members = base_qs.order_by('name')

    # 페이지네이션 -----------------------------------------------------------
    paginator   = Paginator(members, 10)
    page_number = request.GET.get('page', 1)
    page_obj    = paginator.get_page(page_number)

    # 페이지 그룹 계산 -------------------------------------------------------
    total_pages  = paginator.num_pages
    group_size   = 10
    current_group= (page_obj.number - 1) // group_size
    start_page   = current_group * group_size + 1
    end_page     = min(start_page + group_size - 1, total_pages)
    custom_page_range = range(start_page, end_page + 1)

    # object_list 가공 ------------------------------------------------------
    modified_members = []
    for member in page_obj.object_list:
        committee_str = member.committee
        if committee_str and ',' in committee_str:
            committee_str = committee_str.split(',')[0] + ' 등'

        modified_members.append({
            'name'     : member.name,
            'committee': committee_str,
            'party'    : member.party,
            'image_url': member.image_url,
            'origin'   : member.origin,
            'mona_cd'  : member.mona_cd,
        })

    page_obj.object_list = modified_members  # ▲ 템플릿에 그대로 넘김

    # 템플릿 렌더 ------------------------------------------------------------
    return render(
        request,
        'main/main.html',
        {
            'members'            : page_obj,
            'custom_page_range'  : custom_page_range,
            'has_previous_group' : start_page > 1,
            'has_next_group'     : end_page < total_pages,
            'previous_group_page': start_page - 1,
            'next_group_page'    : end_page + 1,
            'request'            : request
        }
    )


def redirect_to_vote(request, mona_cd):
    member = get_object_or_404(AssemblyMember, mona_cd=mona_cd)
    return redirect('vote:member_detail', mona_cd=mona_cd)
