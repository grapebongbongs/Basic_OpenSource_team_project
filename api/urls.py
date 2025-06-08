from django.urls import path
from .views import (
    search_bills,
    calendar_events, calendar_page,
    party_map_view, party_data_api, representative_data_api
)

urlpatterns = [
    
    path('bills/', search_bills, name='bill-search'),
    path('json/', search_bills, name='bill-search-api'),
    path('calendar/', calendar_page, name='calendar-page'),  # calendar 페이지
    path('calendar/events/', calendar_events, name='calendar-events'),  # 이벤트 로딩
    
    # 지도 관련 기능
    path('map/', party_map_view, name='party-map'),
    
    # API 경로
    path('party-data/', party_data_api, name='party-data'),
    path('representative-data/', representative_data_api, name='representative-data'),

]





