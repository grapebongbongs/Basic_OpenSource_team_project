from django.urls import path
from .views import (
    search_bills, search_page,
    calendar_events, calendar_page,
    party_map_view, party_data_api  # ← 새로 추가할 뷰
)

urlpatterns = [
    # 기존 기능
    path('', search_page, name='bill-search-page'),
    path('bills/', search_bills, name='bill-search'),
    path('json/', search_bills, name='bill-search-api'),
    path('events/', calendar_events, name='calendar-events'),
    path('calendar/', calendar_page, name='calendar-page'),
    path('map/', party_map_view, name='party-map'),
    path('map/data/', party_data_api, name='party-data'),
    path('party-data/', party_data_api, name='party-data'),
]
