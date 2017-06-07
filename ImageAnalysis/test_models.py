from django.test import TestCase

from datetime import datetime
from ImageAnalysis.models import Camera, UploadFile, Image, Source, SourceInImage

class ModelsTest(TestCase):

    def test_image_load_data(self):
        testImage = self.createImage()
        testImage.loadData()
        self.assertTrue(testImage.data is not None)

    def test_get_background(self):
        testImage = self.createImage()
        testImage.getBackground()
        self.assertTrue(testImage.backMean is not None)

    def test_get_stars(self):
        testImage = self.createImage()
        testImage.getStars()
        self.assertTrue(testImage.stars is not None)

    def test_photometry(self):
        testImage = self.createImage()
        testImage.doPhotometry()
        self.assertTrue(testImage.magnitudes is not None)

    def createImage(self):
        c = Camera(cameraName="Bob", xSize=1, ySize=1)
        c.save()
        uf = UploadFile(file='./testimage10.fits')
        uf.save()
        t = datetime.now()
        i = Image(cameraFilter='R', camera=c, imageFile=uf, obsTime=t, previewName='x.png')
        i.save()
        return i
