from django.conf.urls import patterns, url
from views import Weixin

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', Weixin.as_view()),
)
