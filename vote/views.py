from django.shortcuts import render
from vote.models import Vote

def member_list(request):
    votes = Vote.objects.select_related('bill', 'member').all()
    return render(request, 'member/member.html', {'votes': votes})