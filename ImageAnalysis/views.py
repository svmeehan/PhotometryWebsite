from django.shortcuts import render, redirect

from django.http import HttpResponse

from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
 
from .forms import UploadFileForm
from .models import UploadFile, Image, Camera, Source, SourceInImage

def index(request):
	return HttpResponse("Index Page")

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
					image.save()
					image.getRealWorldMagnitudes()
					image.createPreviewImage()

					print(len(image.stars))
					#print('refs:\n', image.references)
					#print('matching refs:\n', image.getReferencesInImage())
					print(image.offset, ' +/- ', image.offsetErr)
					#print(image.backMean, image.backStd)
					#print(Source.objects.filter(RA__range=(118.16, 118.169)).filter(DEC__range=(30.077, 30.078)))
					print(len(image.realMagnitudes))
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


def results(request):
	print('In results controller')
	print(request.GET)
	return render(request, 'ImageAnalysis/results.html')

def object(request, object_id=None):
	if object_id is not None:
		source = Source.objects.get(pk=object_id)
		return render(request, 'ImageAnalysis/object.html', {'source': source})
	else:
		return HttpResponse("object search page")

def lightcurve(request, object_id=None):
	if object_id is not None:
		source = Source.objects.get(pk=object_id)
		observations = source.sourceinimage_set.all()
		for observation in observations:
			x.append(observation.image.time)
			y.append(observation.brightness)
		

		return render(request, 'ImageAnalysis/lightcurve.html')
	else:
		return HttpResponse("lightcurve search page")

def basetest(request):
	return render(request, 'ImageAnalysis/base.html')