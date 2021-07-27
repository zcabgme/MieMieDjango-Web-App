from django import forms
from .models import *


class BubbleChartAdd(forms.ModelForm):
    author_id = forms.IntegerField(min_value=0, max_value=None, required=True)
    fullName = forms.CharField(max_length=300, required=True)
    affiliation = forms.CharField(max_length=2000, required=True)

    class Meta:
        model = UserProfileAct
        fields = ["author_id", "fullName", "affiliation", "approach",
                  "specialty"]
