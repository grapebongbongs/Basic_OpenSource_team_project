from django.urls import path
from .views import bill_list

urlpatterns = [
    path('', bill_list, name='bill_list'),
]