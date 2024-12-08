from django.urls import path, re_path
from .views import (
    AddGradeCheckView,
    UpdateGradeCheckView,
    ListGradeChecksView,
    SearchGradeChecksView,
    GetBadgeView
)

app_name = 'badger'

urlpatterns = [
    path('add/', AddGradeCheckView.as_view(), name='add-grade'),
    path('update/', UpdateGradeCheckView.as_view(), name='update-grade'),
    path('list/', ListGradeChecksView.as_view(), name='list-grades'),
    path('search/', SearchGradeChecksView.as_view(), name='search-grades'),
    path('badge/<str:username>/<str:repository>/', GetBadgeView.as_view(), name='get-badge'),
]