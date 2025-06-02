from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from members.models import AssemblyMember
from vote.models import Vote
from agendas.models import Bill
from django.db.models import Count, Q
from utils.attendance_reader import get_member_attendance_from_424
from utils.attendance_reader import get_member_attendance_20
from utils.attendance_reader import get_member_attendance_21
import os
from django.conf import settings

def member_detail(request, mona_cd):
    member = get_object_or_404(AssemblyMember, mona_cd=mona_cd)

    # 표결 결과를 최신 순으로 정렬
    vote_list = member.votes.select_related('bill').order_by('-bill__rgs_proc_dt')

    # 페이지네이션 설정
    paginator = Paginator(vote_list, 10)
    page_number = request.GET.get('page')
    if not page_number:
        page_number = 1
    else:
        page_number = int(page_number)
    page_obj = paginator.get_page(page_number)  # 현재 페이지의 객체들


    # 페이지 그룹 계산
    total_pages = paginator.num_pages
    group_size = 10
    current_group = (page_number - 1) // group_size
    start_page = current_group * group_size + 1
    end_page = min(start_page + group_size - 1, total_pages)

    custom_page_range = range(start_page, end_page + 1)

    offset = (page_obj.number - 1) * page_obj.paginator.per_page

    # 의원이 발의한 법률안 (이름이 proposer에 포함됨)
    proposed_bills = Bill.objects.filter(proposer__icontains=member.name)




    # 출석률
    excel_path_20 = os.path.join(settings.BASE_DIR, 'static', 'excels', '(열려라국회) 20대 국회 본회의 출석부.xlsx')
    excel_path_21 = os.path.join(settings.BASE_DIR, 'static', 'excels', '(열려라국회) 21대 국회 본회의 출석부.xlsx')
    excel_path_22 = os.path.join(settings.BASE_DIR, 'static', 'excels', '제424회국회(임시회) 본회의 출결현황.xlsx')
    



    attendance = None

    selected_unit = request.GET.get('unit')

    # unit 값에 따라 다른 출결정보 등 처리 가능
    if selected_unit == '20':
        attendance = get_member_attendance_20(excel_path_20, member.name, member.party)
        pass
    elif selected_unit == '21':
        attendance = get_member_attendance_21(excel_path_21, member.name, member.party)
        pass
    elif selected_unit == '22':
        attendance = get_member_attendance_from_424(excel_path_22, member.name, member.party)
        pass
    



    context = {
        'member': member,

        'votes': page_obj,  # 페이지네이션된 객체
        'proposed_bills': proposed_bills,
        'custom_page_range': custom_page_range,
        'has_previous_group': start_page > 1,
        'has_next_group': end_page < total_pages,
        'previous_group_page': start_page - 1,
        'next_group_page': end_page + 1,
        'offset': offset,

        'attendance' : attendance,
        'selected_unit' : selected_unit,
    }

    return render(request, 'member/member.html', context)