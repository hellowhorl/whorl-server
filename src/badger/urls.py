from django.urls import path, re_path
from .views import (
    SubmitGradeCheckView,
    ListGradeChecksView,
    GetBadgeView
)

app_name = 'badger'

urlpatterns = [
    re_path(r'^submit/?$', SubmitGradeCheckView.as_view(), name='submit-grade'),
    re_path(r'^list/?$', ListGradeChecksView.as_view(), name='list-grades'),
    re_path(r'^badge/(?P<username>[\w-]+)/(?P<repository>[\w-]+)/?$', 
            GetBadgeView.as_view(), name='get-badge'),
]