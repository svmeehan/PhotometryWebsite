from django.db import models

# Create your models here.
class Source(models.Model):
	RA = models.FloatField(default=0.0)
	DEC = models.FloatField(default=0.0)
	def __str__(self):
		return str(self.RA) + str(self.DEC)

class Camera(models.Model):
	cameraName = models.CharField(max_length=40)
	xSize = models.IntegerField(default=0)
	ySize = models.IntegerField(default=0)

	def __str__(self):
		return self.cameraName 

class Image(models.Model):
	imagePath = models.CharField(max_length=200)
	sources = models.ManyToManyField(Source, through='SourceInImage', blank=True)
	camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
	cameraFilter = models.CharField(max_length=2)

	def __str__(self):
		return self.imagePath

class SourceInImage(models.Model):
	image = models.ForeignKey(Image, on_delete=models.CASCADE)
	source = models.ForeignKey(Source, on_delete=models.CASCADE)
	brightness = models.FloatField(default=0.0)

