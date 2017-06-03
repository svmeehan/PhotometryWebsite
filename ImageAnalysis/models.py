from django.db import models

#imports for Image class

from astropy.io import fits
from astropy.stats import sigma_clipped_stats
import astropy.coordinates as coord
from photutils import DAOStarFinder, centroid_com, CircularAperture, aperture_photometry
from astroquery.vizier import Vizier
import astropy.units as u
from astropy import wcs

import math as ma
import numpy as np
#for image generation
import matplotlib.pyplot as plt
from astropy.visualization import astropy_mpl_style
from astropy.visualization import (ImageNormalize, ZScaleInterval, MinMaxInterval)
plt.style.use(astropy_mpl_style)
from scipy.ndimage.filters import *

from datetime import datetime

# Create your models here.
class Source(models.Model):
    RA = models.FloatField(default=0.0)
    DEC = models.FloatField(default=0.0)
    def __str__(self):
        return str(self.RA) + " " + str(self.DEC)

class Camera(models.Model):
    cameraName = models.CharField(max_length=40)
    xSize = models.IntegerField(default=0)
    ySize = models.IntegerField(default=0)

    def __str__(self):
        return self.cameraName

class UploadFile(models.Model):
    file = models.FileField(upload_to='ImageAnalysis/static/astroImages/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return str(self.file)

class SourceInImage(models.Model):
    image = models.ForeignKey('Image', on_delete=models.CASCADE)
    source = models.ForeignKey(Source, on_delete=models.CASCADE)
    brightness = models.FloatField(default=0.0)
    def __str__(self):
       return str(self.source) + " @ " + str(self.brightness)

class Image(models.Model):

    #database stored fields

    sources = models.ManyToManyField(Source, through='SourceInImage', blank=True)
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
    cameraFilter = models.CharField(max_length=2)
    imageFile = models.OneToOneField(UploadFile, on_delete=models.CASCADE)
    offset = models.FloatField(default=25.0)
    imageName = models.CharField(max_length=100)
    previewName = models.CharField(max_length=100)
    obsTime = models.DateTimeField()


    path = None #we can use Image.imageFile to return this
    data = None
    header = None

    # Other parameters maybe needed
    offset = None #definitely add this to database
    offsetErr = None
    centreCoordinates = None #add this for image coordinate search 
    #pixelSize = None #TODO: check if this is used
    

    # background parameters
    backMean = None
    backMedian = None
    backStd = None
    # TODO: sort out this duck typing nonsense
    stars = None
    # The magnitudes of the sources in the stars array. Indexed to coincide with stars.
    magnitudes = None
    references = None
    wcsOb = None
    
    realMagnitudes = None



    #imageXsize = None
    #imageYsize = None

    def __str__(self):
        return str(self.imageFile.file)

    def loadData(self):
        self.path = str(self.imageFile.file)
        hdulist = fits.open(self.path)
        self.data = hdulist[0].data
        #self.imageXsize = data.shape[1]
        #self.imageYsize = data.shape[0]
        self.header = hdulist[0].header
        try:
            self.cameraFilter = self.header['FILTER']
        except:
            self.cameraFilter = 'UNK'
        self.obsTime = self.getTime()
        print(self.cameraFilter)
        print(str(self.obsTime))
        hdulist.close()

    def getBackground(self):
        if self.data is not None:
            self.backMean, self.backMedian, self.backStd = sigma_clipped_stats(self.data, sigma=3.0, iters=5)
        else:
            self.loadData()

    def getImageStats(self):
        pass

    def getStars(self):
        if self.backMedian is not None:
            #TODO FWHM: needs to be adjusted based on image size
            self.stars = DAOStarFinder(fwhm=5, threshold=(5 * self.backStd), exclude_border=True)\
                .find_stars(self.data - self.backMedian).as_array().tolist()
        else:
            self.getBackground()
            self.getStars()

    def saveRegions(self):
        if self.stars is not None:
            with open('/home/smeehan/test.reg', 'w') as f: #self.path + ".reg"
                for source in self.stars:
                    region = "circle " + str(source[1]) + " " + str(source[2]) + " 5\n"
                    f.write(region)
        else:
            self.getStars()
            self.saveRegions()

    def centerStars(self):
        if self.stars is not None:
            goodStars = []
            for source in self.stars:
                source = list(source)
                starX = source[1]
                starY = source[2]
                subSize = 5 # Generate based on image size
                #print(self.data.shape[0], self.data.shape[1])
                if subSize <= starX <= self.data.shape[1] - subSize \
                        and subSize <= starY <= self.data.shape[0] - subSize:
                    # get an appropriately sized sub image to centroid in
                    subimage = self.data[(int(starY) - subSize):(int(starY) + subSize),
                                         (int(starX) - subSize):(int(starX) + subSize)]
                    subX, subY = centroid_com(subimage)
                    newX = (starX - subSize) + subX
                    newY = (starY - subSize) + subY
                    if abs(newX - starX) < (subSize / 2) or abs(newY - starY) < (subSize / 2):
                        source[1] = newX
                        source[2] = newY
                        goodStars.append(source)
                        #print("source accepted")
                    #else:
                        #print(starX, starY, "source moved too much")
                #else:
                    #print(starX, starY, "source too close to edge")
                    #print(subSize, starX, self.data.shape[0] - subSize)
                    #print(subSize, starY, self.data.shape[1] - subSize)
            self.stars = goodStars
        else:
            self.getStars()
            self.centerStars()

    def saveStars(self):
        if self.wcsOb is None:
            self.getWCS()
        sourceObjects = []
        for source in self.stars:
            RA, DEC = self.wcsOb.all_pix2world(source[1], source[2], 0)
            existingSource = Source.objects.filter(RA__range=(RA-0.0005, RA+0.0005)).filter(DEC__range=(DEC-0.0005, DEC+0.0005)) # if source is within 2''
            if len(existingSource) == 0:
                newSource = Source(RA=RA, DEC=DEC)
                newSource.save()
                sourceObjects.append(newSource)
            else:
                #print(existingSource[0])
                sourceObjects.append(existingSource[0])
        self.stars = sourceObjects

    def doPhotometry(self):
        if self.stars is not None:
            positions = []
            for source in self.stars:
                x, y = self.wcsOb.all_world2pix(source.RA, source.DEC, 0)
                positions.append((x, y))
            # TODO: adjust aperture size 
            apertures = CircularAperture(positions, r=6)
            photResults = aperture_photometry(self.data, apertures).as_array()
            #print(photResults)
            magnitudes = []
            for row in photResults:
                magnitudes.append(-2.5 * ma.log(row[3], 10))

            self.magnitudes = magnitudes
        else:
            self.getStars()
            self.centerStars()
            self.saveStars()

    def getReferences(self):
        # catalogStars = Vizier.get_catalogs()
        # TODO: width should be adjustable 
        # TODO: need to add filters...
        referenceStars = Vizier.query_region(self.getImageSkyCoords(), width="15m", catalog=["UCAC"])
        referenceStars = referenceStars[2].as_array().tolist()
        references = []
        for star in referenceStars:
            references.append([star[0], star[1], star[16]])
        #print(referenceStars[0][16])
        #if self.wcsOb is None:
        #    self.getWCS()
        #references = []
        #for star in referenceStars:
        #    imX, imY = self.wcsOb.all_world2pix(star[0], star[1], 0)
        #    if 0 < imX < self.data.shape[0] and 0 < imY < self.data.shape[1]:
        #        references.append([float(imX), float(imY), star[16]])

        self.references = references

    def getReferencesInImage(self):
        onImage = []
        #self.stars = self.stars[449:451]
        for reference in self.references:
            for i, source in enumerate(self.stars):
                #print(source.RA, source.DEC, reference[0], reference[1])
                if (source.RA - 0.0005) < reference[0] < (source.RA + 0.0005) \
                 and (source.DEC - 0.0005) < reference[1] < (source.DEC + 0.0005):
                    if reference[2] is not None:
                        #print(onImage)
                        onImage.append([self.magnitudes[i], reference[2]])
                        #print(reference[2])
        #print(len(onImage))
        return onImage

    def getOffset(self):
        """ We calculate the difference between references and the measured magnitudes"""
        refFound = self.getReferencesInImage()
        #print(refFound)
        offsets = []
        for found in refFound:
            #print(found)
            offsets.append(found[1] - found[0])
        #print('OFFSETS:\n',offsets)
        #self.offset = np.mean(offsets)
        #self.offsetErr = np.std(offsets)
        self.offset, offsetMedian, self.offsetErr = sigma_clipped_stats(offsets, sigma=2.0, iters=5)

    def getRealWorldMagnitudes(self):
        self.save()
        realMags = []
        for index, star in enumerate(self.stars):
            #x, y = self.wcsOb.all_pix2world(star[1], star[2], 0)
            mag = self.magnitudes[index] + self.offset
            realMags.append([star, mag])
            newSourceInImage = SourceInImage(image=self, source=star, brightness=mag)
            newSourceInImage.save()
        self.realMagnitudes = realMags

    def getImageSkyCoords(self):
        centerX = int(self.data.shape[0] / 2)
        centerY = int(self.data.shape[0] / 2)
        if self.wcsOb is None:
            self.getWCS()
        RA, DEC = self.wcsOb.wcs_pix2world(centerX, centerY, 0)
        skyCoord = coord.SkyCoord(ra=RA * u.deg, dec=DEC * u.deg)
        return skyCoord

    def getWCS(self):
        if self.wcsOb is None:
            self.wcsOb = wcs.WCS(self.header)

    def createPreviewImage(self):
        norm = ImageNormalize(data=self.data, interval=ZScaleInterval())
        fig = plt.imshow(self.data, cmap='gray', norm=norm)
        #code to plot source coords
        xSources=[]
        ySources=[]
        for source in self.stars:
            x, y = self.wcsOb.all_world2pix(source.RA, source.DEC, 0)
            xSources.append(x)
            ySources.append(y)
        plt.scatter(x=xSources, y=ySources, s=5)
        plt.axis('off')
        fig.axes.get_xaxis().set_visible(False)
        fig.axes.get_yaxis().set_visible(False)
        self.imageName = self.path.split('/')[3]
        self.previewName = self.imageName.split('.')[0] + '.png'
        plt.savefig('ImageAnalysis/static/images/' + self.previewName, bbox_inches='tight', pad_inches=0) 

    def getTime(self):
        if self.header is not None:
            # maybe try date-obs first
            for key, value in self.header.items():
                print(value)
                try:
                    if len(value.split('-')) == 3 and len(value.split('T')) != 2:
                        print('found date part')
                        year = value.split('-')[0]
                        month = value.split('-')[1]
                        day = value.split('-')[2]
                except:
                    pass
                try:    
                    if len(value.split(':')) == 3 and len(value.split('T')) != 2:
                        print('found time part')
                        hour = value.split(':')[0]
                        minute = value.split(':')[1]
                        second = value.split(':')[2]
                except:
                    pass
                try:
                    if len(value.split('T')) == 2 and len(value.split('-')) == 3 and len(value.split(':')) == 3 and value.contains(' ') == False:
                        print('found combo date time')
                        date = value.split('T')[0]
                        time = value.split('T')[1]
                        year = date.split('-')[0]
                        month = date.split('-')[1]
                        day = date.split('-')[2]
                        hour = time.split(':')[0]
                        minute = time.split(':')[1]
                        second = time.split(':')[2]
                except:
                    pass

            if year is not None and month is not None and day is not None\
             and hour is not None and minute is not None and second is not None:
                return datetime(year=int(year), month=int(month), day=int(day), hour=int(hour), minute=int(minute), second=int(float(second)))
            else:
                return datetime.utcnow()
        else:
            self.loadData()

