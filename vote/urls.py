from django.urls import path
from . import views

app_name='vote'

urlpatterns = [
    path('<str:mona_cd>/', views.member_detail, name='member_detail'),
]