from django.urls import path
from .views import member_list

urlpatterns = [
    path('', member_list, name='member_list'),
]

