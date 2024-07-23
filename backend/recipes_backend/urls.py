"""
URL-маршруты Django проекта.

Этот модуль определяет URL-маршруты для вашего Django приложения.
Он включает маршруты для административной панели,
и подключения URL-маршрутов из приложений api.

"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/', include('urlshortner.urls')),
    path('api/docs/', TemplateView.as_view(template_name='redoc.html')),
    path('api/docs/openapi-schema.yml',
         serve,
         {'document_root': settings.BASE_DIR / 'docs',
          'path': 'openapi-schema.yml'})
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
