from __future__ import unicode_literals
from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from django.views.static import serve



urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include('lbe.urls', namespace='lbe')),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    url(r'^grappelli/', include('grappelli.urls')),
    
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
if settings.DEBUG is False:
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
   ]




handler404 = 'lbe.views.e404'
