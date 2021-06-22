from django import forms
from .models import Module, Publication, Approach, Specialty

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ["Department_Name", "Department_ID", "Module_Name", "Module_ID", "Faculty",
                  "Credit_Value", "Module_Lead", "Catalogue_Link", "Description"]
class CheckBoxForm(forms.Form):
    Modules = forms.BooleanField()
    Publications = forms.BooleanField()

class RangeInput(forms.Form):
    publication_range = forms.IntegerField(max_value=Publication.objects.count())
    module_range = forms.IntegerField(max_value=Module.objects.count())

class searchForm(forms.Form):
	approach = forms.ModelChoiceField(queryset=Approach.objects.all())
	specialty = forms.ModelChoiceField(queryset=Specialty.objects.all())
