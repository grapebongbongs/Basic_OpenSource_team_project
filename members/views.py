from django.shortcuts import render
from .models import AssemblyMember
from utils.members_handler import fetch_and_store_members

def member_list(request):
    members = AssemblyMember.objects.order_by('name')
    return render(request, 'members/member_list.html', {'members': members})


def update_and_show_members(request):
    fetch_and_store_members()
