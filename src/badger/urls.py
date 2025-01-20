from django.urls import path
from .views import (
    AddGradeCheckView,
    ListBadgesView,
    GetBadgeView
)

app_name = 'badger'

urlpatterns = [
    path('add/', AddGradeCheckView.as_view(), name='add-grade'),
    path('badges/', ListBadgesView.as_view(), name='list-badges'),
    path('badge/<str:username>/<str:repository>/<str:badge_name>/', GetBadgeView.as_view(), name='get-badge'),
]