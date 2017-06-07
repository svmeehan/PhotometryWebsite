from django.shortcuts import render, redirect

from django.http import HttpResponse

from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
 
from .forms import UploadFileForm, ObjectSearchForm
from .models import UploadFile, Image, Camera, Source, SourceInImage

import matplotlib.pyplot as plt


def index(request):
	"""View for our homepage. Displays the last 10 images analysed"""
	images = Image.objects.all() #get all images
	numberImages = len(images)
	if numberImages < 10:
		imagesToDisplay = numberImages
	else:
		imagesToDisplay = 10
	images = images[numberImages-imagesToDisplay:numberImages] #get last 10 images or all images if there's not 10
	images = images[::-1] #reverse list
	return render(request, 'ImageAnalysis/index.html', {'images': images})

def upload(request):
	"""This view manages the upload of files. It also does the analysis"""
	if request.method == 'POST':
		files = request.FILES.getlist('files')
		images = []
		for f in files: #for each uploaded file
			form = UploadFileForm(request.POST, {'file': f})
			if form.is_valid():
				print('form data valid')
				newFile = UploadFile(file = f)
				if str(f).endswith('.fits'):
					print('saving image and starting analysis')
					newFile.save()
					image = Image(imageFile=newFile, cameraFilter='R', camera=Camera.objects.get(pk=1))
					image.doPhotometry()
					image.getReferences()
					image.getOffset()
					image.getRealWorldMagnitudes()
					image.createPreviewImage()
					image.save()
					images.append(image)

		return render(request, 'ImageAnalysis/results.html', {'images': images})
	else:
		form = UploadFileForm()

	data = {'form': form}
	return render(request, 'ImageAnalysis/upload.html', data)

def object(request, object_id=None):
	"""This allows a user to search objects or browse a specific one"""
	if object_id is not None:
		source = get_object_or_404(Source, pk=object_id)
		return render(request, 'ImageAnalysis/object.html', {'source': source})
	else:
		if len(request.GET) > 0:
			form = ObjectSearchForm(request.GET)
			if form.is_valid():
				RA = float(request.GET['RA'])
				DEC = float(request.GET['DEC'])
				results = Source.objects.filter(RA__range=(RA-0.02, RA+0.02)).filter(DEC__range=(DEC-0.02, DEC+0.02))
				if len(results) > 0:
					return render(request, 'ImageAnalysis/objectresults.html', {'results': results})
				else:
					return render(request, 'ImageAnalysis/noresults.html')
		else:
			form = ObjectSearchForm()

		return render(request, 'ImageAnalysis/objectsearch.html', {'form': form})

def lightcurve(request, object_id=None):
	"""This allows a user to browse a sepcific lightcurve or to search for a specific object"""
	if object_id is not None:
		source = get_object_or_404(Source, pk=object_id)
		observations = source.sourceinimage_set.all() #todo: orderby time
		firstObsTime = observations[0].image.obsTime
		x=[]
		y=[]
		for observation in observations:
			x.append((observation.image.obsTime - firstObsTime).total_seconds())
			y.append(observation.brightness)
		plt.scatter(x=x, y=y)
		plotImageName = 'lightcurve'+ object_id +'.png'
		plt.savefig('ImageAnalysis/static/images/' + plotImageName)
		plt.clf()
		return render(request, 'ImageAnalysis/lightcurve.html', {'lcName': plotImageName, 'source': source})
	else:
		print(request.GET)
		if len(request.GET) > 0:
			form = ObjectSearchForm(request.GET)
			if form.is_valid():
				RA = float(request.GET['RA'])
				DEC = float(request.GET['DEC'])
				results = Source.objects.filter(RA__range=(RA-0.02, RA+0.02)).filter(DEC__range=(DEC-0.02, DEC+0.02))
				if len(results) > 0:
					return render(request, 'ImageAnalysis/lightcurveresults.html', {'results': results})
				else:
					return render(request, 'ImageAnalysis/noresults.html')
		else:
			form = ObjectSearchForm()

		return render(request, 'ImageAnalysis/objectsearch.html', {'form': form})

def image(request, object_id=None):
	"""find or view an image"""
	if object_id is not None:
		image = get_object_or_404(Image, pk=object_id)
		return render(request, 'ImageAnalysis/image.html', {'image': image})
	else:
		if len(request.GET) > 0:
			form = ObjectSearchForm(request.GET)
			if form.is_valid():
				RA = float(request.GET['RA'])
				DEC = float(request.GET['DEC'])
				print(RA, DEC)
				results = Source.objects.filter(RA__range=(RA-0.02, RA+0.02)).filter(DEC__range=(DEC-0.02, DEC+0.02))
				results = results[0].image_set.all()
				if len(results) > 0:
					print('rendering image results')
					return render(request, 'ImageAnalysis/imageresults.html', {'results': results})
				else:
					return render(request, 'ImageAnalysis/noresults.html')
		else:
			form = ObjectSearchForm()
		return render(request, 'ImageAnalysis/objectsearch.html', {'form': form})