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


    def __str__(self):
        return str(self.imageFile.file)

    def loadData(self):
        """ Get the data from the image along with the header and save them in their fields """
        self.path = str(self.imageFile.file)
        hdulist = fits.open(self.path)
        self.data = hdulist[0].data
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
            self.getBackground()

    def getStars(self):
        """ Detect sources in te image """
        if self.backMedian is not None:
            self.stars = DAOStarFinder(fwhm=5, threshold=(5 * self.backStd), exclude_border=True)\
                .find_stars(self.data - self.backMedian).as_array().tolist()
        else:
            self.getBackground()
            self.getStars()

    def saveRegions(self):
        """ This outputs a region file for ds9
            This is x, y, shape, shape size
        """
        if self.stars is not None:
            with open('/home/smeehan/test.reg', 'w') as f: #self.path + ".reg"
                for source in self.stars:
                    region = "circle " + str(source[1]) + " " + str(source[2]) + " 5\n"
                    f.write(region)
        else:
            self.getStars()
            self.saveRegions()

    def centerStars(self):
        """ We centroid stars using a centre of mass calculation """
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
        """ We save the detected sources to the database """
        if self.wcsOb is None:
            self.getWCS()
        sourceObjects = []
        for source in self.stars:
            RA, DEC = self.wcsOb.all_pix2world(source[1], source[2], 0)
            existingSource = Source.objects.filter(RA__range=(RA-0.0005, RA+0.0005)).filter(DEC__range=(DEC-0.0005, DEC+0.0005)) 
            if len(existingSource) == 0: 
                newSource = Source(RA=RA, DEC=DEC) 
                newSource.save()
                sourceObjects.append(newSource)
            else: # if source is within 2'' get the source already in the database
                #print(existingSource[0])
                sourceObjects.append(existingSource[0])
        self.stars = sourceObjects

    def doPhotometry(self):
        """ We get the instrumental brightness of all sources"""
        if self.stars is not None and type(self.stars[0]) is Source:
            positions = []
            for source in self.stars:
                x, y = self.wcsOb.all_world2pix(source.RA, source.DEC, 0)
                positions.append((x, y))
            apertures = CircularAperture(positions, r=6)
            photResults = aperture_photometry(self.data, apertures).as_array()
            magnitudes = []
            for row in photResults:
                magnitudes.append(-2.5 * ma.log(row[3], 10))

            self.magnitudes = magnitudes
        else:
            self.getStars()
            self.centerStars()
            self.saveStars()
            self.doPhotometry()

    def getReferences(self):
        """ We find references using astroquery to search the UCAC catalog on the Vizier website """
        referenceStars = Vizier.query_region(self.getImageSkyCoords(), width=self.getImageSizeInDegrees(), catalog=["UCAC"])
        referenceStars = referenceStars[2].as_array().tolist()
        references = []
        for star in referenceStars:
            references.append([star[0], star[1], star[16]])

        self.references = references

    def getReferencesInImage(self):
        onImage = []
        for reference in self.references:
            for i, source in enumerate(self.stars):
                if (source.RA - 0.0005) < reference[0] < (source.RA + 0.0005) \
                 and (source.DEC - 0.0005) < reference[1] < (source.DEC + 0.0005):
                    if reference[2] is not None:
                        onImage.append([self.magnitudes[i], reference[2]])
        return onImage

    def getOffset(self):
        """ We calculate the difference between references and the measured magnitudes"""
        refFound = self.getReferencesInImage()
        offsets = []
        for found in refFound:
            offsets.append(found[1] - found[0])
        self.offset, offsetMedian, self.offsetErr = sigma_clipped_stats(offsets, sigma=2.0, iters=5)

    def getRealWorldMagnitudes(self):
        """ Convert the magnitudes in self.mags to real mags """
        self.save()
        realMags = []
        for index, star in enumerate(self.stars):
            mag = self.magnitudes[index] + self.offset
            realMags.append([star, mag])
            newSourceInImage = SourceInImage(image=self, source=star, brightness=mag)
            newSourceInImage.save()
        self.realMagnitudes = realMags

    def getImageSkyCoords(self):
        """ Get the approx cetral sky coordinates """
        centerX = int(self.data.shape[0] / 2)
        centerY = int(self.data.shape[0] / 2)
        if self.wcsOb is None:
            self.getWCS()
        RA, DEC = self.wcsOb.wcs_pix2world(centerX, centerY, 0)
        skyCoord = coord.SkyCoord(ra=RA * u.deg, dec=DEC * u.deg)
        return skyCoord

    def getWCS(self):
        """ We need this object to convert between sky and image coords"""
        if self.wcsOb is None:
            self.wcsOb = wcs.WCS(self.header)

    def createPreviewImage(self):
        """We create an image of the lightcurve plotted with matplotlib"""
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
        """
        We get the time from the image header. We iterate through the header looking fo:
        a date in format YYYY-MM-DD
        and a time in HH:MM:SS
        """
        if self.header is not None:
            # maybe try date-obs first
            for key, value in self.header.items():
                try:
                    if len(value.split('-')) == 3 and len(value.split('T')) != 2:
                        year = value.split('-')[0]
                        month = value.split('-')[1]
                        day = value.split('-')[2]
                except:
                    pass
                try:    
                    if len(value.split(':')) == 3 and len(value.split('T')) != 2:
                        hour = value.split(':')[0]
                        minute = value.split(':')[1]
                        second = value.split(':')[2]
                except:
                    pass
                try:
                    if len(value.split('T')) == 2 and len(value.split('-')) == 3 and len(value.split(':')) == 3 and value.contains(' ') == False:
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
            self.getTime()

    def getImageSizeInDegrees(self):
        xyMax = max(self.data.shape[0], self.data.shape[1])
        RA1, DEC1 = self.wcsOb.wcs_pix2world(0, 0, 0)
        RA2, DEC2 = self.wcsOb.wcs_pix2world(0, 1, 0)
        pixelSize = (abs(RA2 - RA1)**2 + abs(DEC2 - DEC1)**2)**0.5
        imageSize = pixelSize * xyMax
        return str(imageSize)+'d'