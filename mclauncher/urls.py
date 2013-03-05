from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin

from .launcher import views

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^accounts/', include('registration.auth_urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^ping/', include('ping.urls')),
    url(r'^sse$', login_required(views.SSE.as_view()), name="mcl_sse"),
)
 
urlpatterns += patterns('mclauncher.launcher.views',
    url(r'^launch$', 'launch', name="mcl_launch"),
    url(r'^terminate$', 'terminate', name="mcl_terminate"),
    url(r'^$', 'index', name="mcl_index"),
)

urlpatterns += staticfiles_urlpatterns()

# Quick and dirty way to serve static content on Heroku.
if not settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.STATIC_ROOT}),
    )
