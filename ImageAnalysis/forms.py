from django import forms

from .models import UploadFile

class UploadFileForm(forms.ModelForm):
	class Meta:
		model = UploadFile
		fields = "__all__"

class ObjectSearchForm(forms.Form):
	RA = forms.FloatField(label='RA', min_value=0.0, max_value=360.0)
	DEC = forms.FloatField(label='DEC', min_value=0.0, max_value=360.0)