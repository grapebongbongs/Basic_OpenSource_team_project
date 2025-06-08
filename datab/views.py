from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
import os

def upload_db(request):
    if request.method == 'POST' and request.FILES.get('dbfile'):
        db_file = request.FILES['dbfile']
        db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')

        with open(db_path, 'wb+') as destination:
            for chunk in db_file.chunks():
                destination.write(chunk)
        return HttpResponse("✅ DB 업로드 완료")

    return render(request, 'database/upload_db.html')