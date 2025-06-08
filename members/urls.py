from django.urls import path
from .views import update_and_show_main
from .views import redirect_to_vote


from. import views

app_name = 'members'

urlpatterns = [
    path('', update_and_show_main, name='member_list'),
    path('extract/<str:mona_cd>/', redirect_to_vote, name='redirect_to_vote'),
]

