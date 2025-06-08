from django.urls import path
from .views import upload_db  

urlpatterns = [
    path('upload-db/', upload_db),
]