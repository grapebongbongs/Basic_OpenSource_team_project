from django.shortcuts import render
from agendas.models import Bill

def bill_list(request):
    bills = Bill.objects.all().order_by('-propose_dt')
    return render(request, 'agendas/agenda_list.html', {'bills': bills})