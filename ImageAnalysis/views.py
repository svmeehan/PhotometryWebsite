from django.shortcuts import render

from django.http import HttpResponse

def index(request):
	return HttpResponse("Index Page")

def upload(request):
	return HttpResponse("upload page")

def results(request):
	return HttpResponse("results page")

def object(request, object_id):
	return HttpResponse("object details " + str(object_id))

def lightcurve(request, object_id):
	return HttpResponse("lightcurve plot " + str(object_id))