from django.urls import path
from .views import BadgeSearchView, BadgeStepUpdateView, BadgeCollectionView

app_name = 'badger'

urlpatterns = [
    path('search/', BadgeSearchView.as_view(), name='search-badge'),
    path('update/<str:badge_id>/<int:step>/', BadgeStepUpdateView.as_view(), name='update-badge-step'),
    path('collection/<str:username>/', BadgeCollectionView.as_view(), name='badge-collection'),
]