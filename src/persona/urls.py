from .views import *
from django.urls import path

app_name = "persona"

urlpatterns  = [
    path('search/<str:persona_name>', PersonaSearchView.as_view(), name = "persona-search"),
    path('create/<str:persona_name>', PersonaCreateView.as_view(), name = "persona-create"),
    path('generate/<str:persona_name>', SyncPersonaGenerateView.as_view(), name = "persona-generate"),
    path('cancel/<str:thread_id>', PersonaThreadManagementView.as_view(), name = "persona-thread-cancel"),
    path('delete/<str:thread_id>', PersonaThreadManagementView.as_view(), name = "persona-thread-delete"),
]
