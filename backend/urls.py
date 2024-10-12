from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.shortcuts import redirect
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

def home(request):
    """Handle default request"""
    return redirect('/docs/')

schema_view = get_schema_view(
    openapi.Info(
        title="Django OAuth System API",
        default_version='v1',
        description="A ready-to-use Django OAuth system supporting multiple providers, designed for quick integration, enhanced security, and a user-friendly experience.",
        contact=openapi.Contact(email="oluwaseyitemitope456@gmail.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

URL = "api/v1/"

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", home, name="redirect_to_docs"),
    path(URL + "auth/", include('auth_core.urls')),
    path(URL + "oauth/" , include('oauth.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name="schema-swagger-ui"),
        path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name="scehma-redoc")
    ]
