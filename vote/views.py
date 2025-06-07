from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from members.models import AssemblyMember
from vote.models import Vote
from agendas.models import Bill
from django.db.models import Q
from utils.attendance_reader import (
    get_member_attendance_from_424,
    get_member_attendance_20,
    get_member_attendance_21,
)
import os
from django.conf import settings

def member_detail(request, mona_cd):
    member = get_object_or_404(AssemblyMember, mona_cd=mona_cd)

    # ────────────────── ① URL 파라미터 읽기 ──────────────────
    selected_unit = request.GET.get('unit')        # '20' | '21' | '22' | None
    billq         = request.GET.get('billq', '').strip()  # 법안명 키워드
    page_number   = request.GET.get('page', 1)

    # ────────────────── ② 표결(vote) 쿼리셋 필터링 ──────────────────
    vote_qs = member.votes.all()                       # 기본 QS

    # 1) unit(대수) 우선 필터
    if selected_unit and selected_unit.isdigit():
        vote_qs = vote_qs.filter(bill__age=int(selected_unit))

    # 2) billq(법안명) 필터
    if billq:
        vote_qs = vote_qs.filter(bill__bill_name__icontains=billq)

    # 3) bill 조인 + 최신순 정렬  ← ★ 여기서 한 번에 체인
    vote_qs = (
        vote_qs.select_related('bill').order_by('-bill__rgs_proc_dt')            # bill 테이블 조인 # 최신순
    )


    # ────────────────── ③ 페이지네이션 ──────────────────
    paginator = Paginator(vote_qs, 10)
    page_obj  = paginator.get_page(page_number)

    total_pages   = paginator.num_pages
    group_size    = 10
    current_group = (page_obj.number - 1) // group_size
    start_page    = current_group * group_size + 1
    end_page      = min(start_page + group_size - 1, total_pages)
    custom_page_range = range(start_page, end_page + 1)
    offset = (page_obj.number - 1) * page_obj.paginator.per_page

    # ────────────────── ④ 의원이 발의한 법률안 ──────────────────
    proposed_bills = Bill.objects.filter(proposer__icontains=member.name)

    # ────────────────── ⑤ 출석률 엑셀 경로 & 함수 ──────────────────
    excel_path_20 = os.path.join(
        settings.BASE_DIR, 'static', 'excels', '(열려라국회) 20대 국회 본회의 출석부.xlsx')
    excel_path_21 = os.path.join(
        settings.BASE_DIR, 'static', 'excels', '(열려라국회) 21대 국회 본회의 출석부.xlsx')
    excel_path_22 = os.path.join(
        settings.BASE_DIR, 'static', 'excels', '제424회국회(임시회) 본회의 출결현황.xlsx')

    attendance = None
    if selected_unit == '20':
        attendance = get_member_attendance_20(excel_path_20, member.name, member.party, member.origin)
    elif selected_unit == '21':
        attendance = get_member_attendance_21(excel_path_21, member.name, member.party)
    elif selected_unit == '22':
        attendance = get_member_attendance_from_424(excel_path_22, member.name, member.party)


    billq = request.GET.get('billq', '').strip()  #billq 문자열 저장


    # ────────────────── ⑥ 템플릿 컨텍스트 ──────────────────
    context = {
        'member'              : member,
        'votes'               : page_obj,           # 페이지네이션된 표결
        'proposed_bills'      : proposed_bills,
        'custom_page_range'   : custom_page_range,
        'has_previous_group'  : start_page > 1,
        'has_next_group'      : end_page < total_pages,
        'previous_group_page' : start_page - 1,
        'next_group_page'     : end_page + 1,
        'offset'              : offset,
        'attendance'          : attendance,
        'selected_unit'       : selected_unit,
        'billq': billq,  # ← 추가
    }

    return render(request, 'member/member.html', context)
