from django.shortcuts import render, get_object_or_404
from members.models import AssemblyMember
from vote.models import Vote

def member_detail(request, mona_cd):
    # mona_cd에 해당하는 AssemblyMember 객체를 가져온다.
    member = get_object_or_404(AssemblyMember, mona_cd=mona_cd)
    votes = Vote.objects.filter(member=member)

    context = {
        'member': member,
        'votes': votes,
    }

    return render(request, 'member/member.html', context)






