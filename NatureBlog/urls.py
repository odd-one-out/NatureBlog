"""
URL configuration for NatureBlog project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static


from NatureBlog import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('blog.urls', namespace='blog')),
    path('', include('user.urls', namespace='user')),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]


# url для debug toolbar и медиа-файлов добавляются только во время разработки,
# нельзя импортировать ф-цию debug_toolbar_urls() вверху, будет ошибка при тестах!!!
if settings.DEBUG:
    urlpatterns +=  static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if not settings.TESTING:
        urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]

