from django.urls import path, re_path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# API Documentation Schema
schema_view = get_schema_view(
    openapi.Info(
        title="Whorl API",
        default_version='v1',
        description="API documentation for Whorl services",
        contact=openapi.Contact(email="your.email@example.com"),
        license=openapi.License(name="CC0"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# API URL Patterns
urlpatterns = [
    re_path(r'^v1/climate/', include(('climate.urls', 'climate'))),
    re_path(r'^v1/inventory/', include(('inventory.urls', 'inventory'))),
    re_path(r'^v1/omnipresence/', include(('omnipresence.urls', 'omnipresence'))),
    re_path(r'^v1/persona/', include(('persona.urls', 'persona'))),
    re_path(r'^v1/badger/', include(('badger.urls'))),
    
    # API Documentation URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', 
        schema_view.without_ui(cache_timeout=0), 
        name='schema-json'
    ),
    re_path(r'^swagger/$', 
        schema_view.with_ui('swagger', cache_timeout=0), 
        name='schema-swagger-ui'
    ),
]