from . import views
from django.urls import path, re_path

urlpatterns  = [
    path('', views.OmnipresenceView.as_view()),
    re_path(r'update/(?P<pk>\d+)/', views.OmnipresenceUpdateView.as_view()),
    re_path(r'active/', views.OmnipresenceActiveView.as_view()),
    re_path(r'local/', views.OmnipresenceActiveView.as_view())
]
