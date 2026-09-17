from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin-login/', admin.site.urls), # Using admin-login/ instead of admin/ as requested
    path('', include('core.urls')),
    path('departments/', include('departments.urls')),
    path('subjects/', include('subjects.urls')),
    path('papers/', include('papers.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('ai_analysis/', include('ai_analysis.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
