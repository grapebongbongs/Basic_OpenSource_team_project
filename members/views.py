from django.shortcuts import render, get_object_or_404, redirect
from .models import AssemblyMember
from utils.members_handler import fetch_and_store_current_members

def update_and_show_main(request):
    fetch_and_store_current_members()
    modified_members = []
    members = AssemblyMember.objects.order_by('name')
    for member in members:
        c= member.committee
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


