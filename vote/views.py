from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from members.models import AssemblyMember
from vote.models import Vote
from agendas.models import Bill

def member_detail(request, mona_cd):
    member = get_object_or_404(AssemblyMember, mona_cd=mona_cd)

    # 표결 결과를 최신 순으로 정렬
    vote_list = member.votes.select_related('bill').order_by('-bill__rgs_proc_dt')

    # 페이지네이션 설정
    paginator = Paginator(vote_list, 10)
    page_number = request.GET.get('page')
    votes = paginator.get_page(page_number)

    # 페이지 범위 계산 (현재 페이지를 기준으로 -5~+4)
    current = votes.number
    start_page = max(current - 5, 1)
    end_page = min(current + 4, votes.paginator.num_pages)
    custom_range = range(start_page, end_page + 1)

    # 의원이 발의한 법률안 (이름이 proposer에 포함됨)
    proposed_bills = Bill.objects.filter(proposer__icontains=member.name)

    context = {
        'member': member,
        'votes': votes,  # 페이지네이션된 객체
        'proposed_bills': proposed_bills,
        'custom_page_range': custom_range,
    }

    return render(request, 'member/member.html', context)