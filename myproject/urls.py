from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('members.urls')),  # members 앱의 URLs로 위임
    path('api/', include('api.urls')),  # api 앱의 URLs로 위임
    path('agendas/', include('agendas.urls')),  # agendas 앱의 URLs로 위임
    path('vote/', include('vote.urls')),  # vote 앱의 URLs로 위임
    path('upload_db/', include('datab.urls')),
]
