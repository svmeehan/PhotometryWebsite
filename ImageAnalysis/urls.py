from django.conf.urls import url

from . import views

urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^upload/$', views.upload, name='upload'),
	url(r'^results/$', views.results, name='results'),
	url(r'^object/(?P<object_id>[0-9]+)/$', views.object, name='object'),
	url(r'^lightcurve/(?P<object_id>[0-9]+)/$', views.lightcurve, name='lightcurve'),
]