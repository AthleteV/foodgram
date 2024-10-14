from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from foodgram.views import redirect_short_link

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path(
        's/<str:encoded_id>/',
        redirect_short_link,
        name='redirect_short_link'
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
