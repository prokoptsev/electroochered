# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url
from sadiki.logger.views import RequestionLogs

urlpatterns = patterns('',
    url(r'^request/(?P<requestion_id>\d{1,7})/$',
        RequestionLogs.as_view(), name=u'requestion_logs'),
)
