from django.shortcuts import render
from .models import AssemblyMember
from utils.members_handler import fetch_and_store_members

def update_and_show_main(request):
    fetch_and_store_members()
    members = AssemblyMember.objects.order_by('name')
    return render(request, 'main/main.html', {'members': members})
