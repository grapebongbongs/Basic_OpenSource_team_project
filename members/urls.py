from django.urls import path
from .views import update_and_show_main

urlpatterns = [
    path('', update_and_show_main, name='member_list'),
]