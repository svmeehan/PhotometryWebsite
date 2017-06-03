from django.conf.urls import url

from . import views

app_name='imageanalysis'

urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^upload/$', views.upload, name='upload'),
	url(r'^object/$', views.object, name='object'),
	url(r'^object/(?P<object_id>[0-9]+)/$', views.object, name='object'),
	url(r'^lightcurve/$', views.lightcurve, name='lightcurve'),
	url(r'^lightcurve/(?P<object_id>[0-9]+)/$', views.lightcurve, name='lightcurve'),
	url(r'^image/$', views.image, name='image'),
	url(r'^image/(?P<object_id>[0-9]+)/$', views.image, name='image'),

]