from django.urls import path
from .views import (
    BadgeSearchView,
    BadgeStepUpdateView,
    BadgeCollectionView,
    BadgeCreateView,
    GatorCheckSubmitView
)

app_name = 'badger'

urlpatterns = [
    path('search/', BadgeSearchView.as_view(), name='search-badge'),
    path('update/<str:badge_id>/step/<int:step>/', BadgeStepUpdateView.as_view(), name='update-badge-step'),
    path('collection/<str:username>/', BadgeCollectionView.as_view(), name='badge-collection'),
    path('badges/create/', BadgeCreateView.as_view(), name='create-badge'),
    path('submit/', GatorCheckSubmitView.as_view(), name='submit-check'),
]