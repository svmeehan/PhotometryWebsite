from django.shortcuts import render, redirect

from django.http import HttpResponse

from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
 
from .forms import UploadFileForm, ObjectSearchForm
from .models import UploadFile, Image, Camera, Source, SourceInImage

import matplotlib.pyplot as plt

def index(request):
	images = Image.objects.all()
	numberImages = len(images)
	if numberImages < 10:
		imagesToDisplay = numberImages
	else:
		imagesToDisplay = 10
	images = images[numberImages-imagesToDisplay:numberImages]
	images = images[::-1] #reverse list
	return render(request, 'ImageAnalysis/index.html', {'images': images})

def upload(request):
	if request.method == 'POST':
		print(request.POST)
		print(request.FILES)
		print('recieved data')
		files = request.FILES.getlist('files')
		print(files)
		#print(request.FILES.get(keys[0]))
		images = []
		for f in files:
			form = UploadFileForm(request.POST, {'file': f})
			if form.is_valid():
				print('form data valid')		
				print('uploading', str(f))
				newFile = UploadFile(file = f)
				if str(f).endswith('.fits'):
					print('saving image and starting analysis')
					newFile.save()
					image = Image(imageFile=newFile, cameraFilter='R', camera=Camera.objects.get(pk=1)) # test image settings
					#image.save()
					#print(image.imageFile)
					image.loadData()
					image.getBackground()
					image.getStars()
					#print(image.stars[0:3])
					image.centerStars()
					image.saveRegions()
					image.saveStars()
					image.doPhotometry()
					image.getReferences()
					image.getOffset()
					
					image.getRealWorldMagnitudes()
					image.createPreviewImage()
					image.save()

					#print(len(image.stars))
					#print('refs:\n', image.references)
					#print('matching refs:\n', image.getReferencesInImage())
					#print(image.offset, ' +/- ', image.offsetErr)
					#print(image.backMean, image.backStd)
					#print(Source.objects.filter(RA__range=(118.16, 118.169)).filter(DEC__range=(30.077, 30.078)))
					#print(len(image.realMagnitudes))
					images.append(image)
			else:
				print('form invalid')

		return render(request, 'ImageAnalysis/results.html', {'images': images})
	else:
		form = UploadFileForm()

	data = {'form': form}
	return render(request, 'ImageAnalysis/upload.html', data)
	#return render('ImageAnalysis/upload.html')
	#return HttpResponse("upload?")

def object(request, object_id=None):
	if object_id is not None:
		source = Source.objects.get(pk=object_id)
		return render(request, 'ImageAnalysis/object.html', {'source': source})
	else:
		#print(request.GET)
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

		#print(form.RA)
		return render(request, 'ImageAnalysis/objectsearch.html', {'form': form})

def lightcurve(request, object_id=None):
	if object_id is not None:
		source = Source.objects.get(pk=object_id)
		observations = source.sourceinimage_set.all() #todo: orderby time
		firstObsTime = observations[0].image.obsTime
		x=[]
		y=[]
		for observation in observations:
			x.append((observation.image.obsTime - firstObsTime).total_seconds())
			y.append(observation.brightness)
		#print(x)
		#print(y)
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

		#print(form.RA)
		return render(request, 'ImageAnalysis/objectsearch.html', {'form': form})

def image(request, object_id=None):
	if object_id is not None:
		image = Image.objects.get(pk=object_id)
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
					#print(results)
					return render(request, 'ImageAnalysis/imageresults.html', {'results': results})
				else:
					return render(request, 'ImageAnalysis/noresults.html')
		else:
			form = ObjectSearchForm()
		return render(request, 'ImageAnalysis/objectsearch.html', {'form': form})