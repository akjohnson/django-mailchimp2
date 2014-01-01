from django.conf.urls import patterns, url

from .views import IndexView, SubscribeFormView

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='maillist_index'),
    url(r'^(?P<list_id>\w+)/subscribe/$', SubscribeFormView.as_view(),
        name='maillist_subscribe')
)
