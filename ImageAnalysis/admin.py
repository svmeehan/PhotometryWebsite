from django.contrib import admin

from .models import Image, Camera, Source, SourceInImage
# Register your models here.

admin.site.register(Image)
admin.site.register(Camera)
admin.site.register(Source)
admin.site.register(SourceInImage)