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

class Image(models.Model):
	
	#database stored fields

	imagePath = models.CharField(max_length=200)
	sources = models.ManyToManyField(Source, through='SourceInImage', blank=True)
	camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
	cameraFilter = models.CharField(max_length=2)

	def __str__(self):
		return self.imagePath

	# Other fields

	backMean = None
    backMedian = None
    backStd = None
    stars = None
    magnitudes = None
    references = None
    wcsOb = None
    offset = None
    realMagnitudes = None



	    def __init__(self, path):
        self.path = path
        self.hdulist = fits.open(path)
        self.data = self.hdulist[0].data
        self.header = self.hdulist[0].header
        self.hdulist.close()

    def getBackground(self):
        self.backMean, self.backMedian, self.backStd = sigma_clipped_stats(self.data, sigma=3.0, iters=5)

    def getStars(self):
        if self.backMedian is not None:
            self.stars = DAOStarFinder(fwhm=5, threshold=(5 * self.backStd), exclude_border=True)\
                .find_stars(self.data - self.backMedian).as_array().tolist()
        else:
            self.getBackground()
            self.getStars()

    def saveRegions(self):
        if self.stars is not None:
            with open(self.path + ".reg", 'w') as f:
                for line in self.stars:
                    region = "circle " + str(line[0]) + " " + str(line[1]) + " 5\n"
                    f.write(region)
        else:
            self.getStars()
            self.saveRegions()

    def centerStars(self):
        if self.stars is not None:
            goodStars = []
            for row in self.stars:
                row = list(row)
                starX = row[1]
                starY = row[2]
                subSize = 5
                if subSize <= starX <= self.data.shape[0] - subSize \
                        and subSize <= starY <= self.data.shape[1] - subSize:
                    # get an appropriately sized sub image to centroid in
                    subimage = self.data[(int(starY) - subSize):(int(starY) + subSize),
                                         (int(starX) - subSize):(int(starX) + subSize)]
                    subX, subY = centroid_com(subimage)
                    newX = (starX - subSize) + subX
                    newY = (starY - subSize) + subY
                    if abs(newX - starX) < (subSize / 2) or abs(newY - starY) < (subSize / 2):
                        row[1] = newX
                        row[2] = newY
                        goodStars.append(row)
            self.stars = goodStars
        else:
            self.getStars()
            self.centerStars()

    def doPhotometry(self):
        if self.stars is not None:
            positions = []
            for row in self.stars:
                positions.append((row[1], row[2]))
            apertures = CircularAperture(positions, r=6)
            photResults = aperture_photometry(self.data, apertures).as_array()
            #print(photResults)
            magnitudes = []
            for row in photResults:
                magnitudes.append(-2.5 * ma.log(row[3], 10))

            selfsubSize = 5.magnitudes = magnitudes
        else:
            self.getStars()
            self.centerStars()

    def getReferences(self):
        # catalogStars = Vizier.get_catalogs()
        referenceStars = Vizier.query_region(self.getImageSkyCoords(), width="15m", catalog=["UCAC"])
        referenceStars = referenceStars[2]
        #print(referenceStars[0][16])
        if self.wcsOb is None:
            self.getWCS()
        references = []
        for star in referenceStars:
            imX, imY = self.wcsOb.wcs_world2pix(star[0], star[1], 0)
            if 0 < imX < self.data.shape[0] and 0 < imY < self.data.shape[1]:
                references.append([float(imX), float(imY), star[16]])

        self.references = references

    def getReferencesInImage(self):
        onImage =[]
        for reference in self.references:
            for i, star in enumerate(self.stars):
                if (star[1] - 0.1) < reference[0] < (star[1] + 0.1) \
                 and (star[2] - 0.1) < reference[1] < (star[2] + 0.1):
                    onImage.append([self.magnitudes[i], reference[2]])
        return onImage

    def getOffset(self):
        refFound = self.getReferencesInImage()
        offsets = []
        for found in refFound:
            offsets.append(found[1] - found[0])
        self.offset = np.mean(offsets)

    def getRealWorldMagnitudes(self):
        realMags = []
        for index, star in enumerate(self.stars):
            x, y = self.wcsOb.wcs_pix2world(star[1], star[2], 0)
            mag = self.magnitudes[index] + self.offset
            realMags.append([float(x), float(y), mag])
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

class SourceInImage(models.Model):
	image = models.ForeignKey(Image, on_delete=models.CASCADE)
	source = models.ForeignKey(Source, on_delete=models.CASCADE)
	brightness = models.FloatField(default=0.0)
	def __str__(self):
		return str(self.source) + " @ " + str(self.brightness)

