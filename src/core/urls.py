from django.urls import path, re_path, include
from rest_framework.reverse import reverse
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

urlpatterns = [
    re_path(
        r'v1/climate/',
        include(('climate.urls', 'climate'))
    ),
    re_path(
        r'v1/inventory/',
        include(('inventory.urls', 'inventory'))
    ),
    re_path(
        r'v1/omnipresence/',
        include(('omnipresence.urls', 'omnipresence'))
    ),
    re_path(
        r'v1/persona/',
        include(('persona.urls', 'persona'))
    ),
]