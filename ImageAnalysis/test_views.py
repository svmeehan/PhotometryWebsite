from django.test import TestCase

from datetime import datetime
from ImageAnalysis.models import Camera, UploadFile, Image, Source, SourceInImage

class ImageAnalysisViewsTest(TestCase):
    """Test homepage view"""
    def test_index_response(self):
        response = self.client.get('/')
        # make sure 200 return code
        self.assertEqual(response.status_code, 200)

    def test_index_less_than_10_images(self):
        #make sure that page renders when there are not 10 images in the database
        for i in range(5):
            self.addImageToDb()
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # returns a context with images
        self.assertTrue('images' in response.context)
        #there are 5 images (lights?)
        self.assertEqual(len(response.context['images']), 5)

    def test_index_more_than_10_images(self):
        for i in range(10):
            self.addImageToDb()
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # returns a context with images
        self.assertTrue('images' in response.context)
        #there are 5 images (lights?)
        self.assertEqual(len(response.context['images']), 10)

    def test_upload_response(self):
        response = self.client.get('/upload/')
        # make sure 200 return code
        self.assertEqual(response.status_code, 200)

    def test_object_response(self):
        response = self.client.get('/object/')
        # make sure 200 return code
        self.assertEqual(response.status_code, 200)

    def test_oject_with_id_response(self):
        s = Source(RA=0, DEC=0)
        s.save()
        response = self.client.get('/object/1/')
        # make sure 200 return code
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['source'].pk, 1)

    def test_object_with_get_response(self):
        response = self.client.get('/object/?RA=0.0&DEC=0.0')
        # make sure 200 return code
        self.assertEqual(response.status_code, 200)

    def test_image_response(self):
        response = self.client.get('/image/')
        # make sure 200 return code
        self.assertEqual(response.status_code, 200)

    def test_image_with_id_response(self):
        self.addImageToDb()
        response = self.client.get('/image/1/')
        # make sure 200 return code
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['image'].pk, 1)


    def test_lightcurve_response(self):
        response = self.client.get('/lightcurve/')
        # make sure 200 return code
        self.assertEqual(response.status_code, 200)

    def test_lightcurve_with_id_response(self):
        self.addImageToDb()
        s = Source(RA=0, DEC=0)
        s.save()
        sii = SourceInImage(image = Image.objects.get(pk=1), source=s, brightness=24)
        sii.save()
        response = self.client.get('/lightcurve/1/')
        # make sure 200 return code
        self.assertEqual(response.status_code, 200)
        #self.assertTrue(source in response.context)
        #self.assertTrue(lcName in response.context)

    def test_lightcurve_with_get_response(self):
        response = self.client.get('/lightcurve/?RA=0.0&DEC=0.0')
        # make sure 200 return code
        self.assertEqual(response.status_code, 200)

    def addImageToDb(self):
        c = Camera(cameraName="Bob", xSize=1, ySize=1)
        c.save()
        uf = UploadFile(file='/mock/')
        uf.save()
        t = datetime.now()
        i = Image(cameraFilter='R', camera=c, imageFile=uf, obsTime=t, previewName='x.png')
        i.save()