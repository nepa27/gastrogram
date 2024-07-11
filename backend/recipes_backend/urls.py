"""
URL-маршруты Django проекта.

Этот модуль определяет URL-маршруты для вашего Django приложения.
Он включает маршруты для административной панели,
и подключения URL-маршрутов из приложений api.

"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/', include('urlshortner.urls')),
]
