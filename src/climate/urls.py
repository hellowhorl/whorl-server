from django.urls import re_path, path
from .views import ClimateDataViewAll

urlpatterns = [
    path('', ClimateDataViewAll.as_view(), name='climate-all'),
]
