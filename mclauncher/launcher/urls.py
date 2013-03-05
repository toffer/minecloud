from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = patterns('',
    url(r'^$', views.index, name="mcl_index"),
    url(r'^launch$', views.launch, name="mcl_launch"),
    url(r'^terminate$', views.terminate, name="mcl_terminate"),
    url(r'^sse$', login_required(views.SSE.as_view()), name="mcl_sse"),
)