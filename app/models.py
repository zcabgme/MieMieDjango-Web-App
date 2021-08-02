from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.postgres.fields import ArrayField
import json

class Module(models.Model):
    Department_Name = models.CharField(max_length=400)
    Department_ID = models.CharField(max_length=200)
    Module_Name = models.CharField(max_length=400)
    Module_ID = models.CharField(max_length=200)
    Faculty = models.CharField(max_length=400)
    Credit_Value = models.IntegerField(default=0, blank=True, null=True)
    Module_Lead = models.CharField(max_length=200, null=True, blank=True)
    Catalogue_Link = models.CharField(max_length=400)
    Description = models.TextField(null=True, blank=True)
    # Last_Updated = models.DateTimeField
    assignedSDG = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.Module_ID + ': ' + self.Module_Name

    def get_absolute_url(self):
        return f"/module/{self.pk}"
    class Meta:
        ordering = ['-id']


class Publication(models.Model):
    title = models.TextField(blank=True)
    doi = models.CharField(max_length=100, blank=True)
    data = models.JSONField(null=True, blank=True)
    assignedSDG = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.title
    class Meta:
        ordering = ['-id']

    def get_absolute_url(self):
        return f"/publication/{self.pk}"


class PyChart(models.Model):
    name = models.CharField(max_length=100, blank=True)
    picture = models.ImageField(
        null=True, blank=True, upload_to='charts/', default='')


class ColorAct(models.Model):
    color = models.CharField(max_length=50)

    def __str__(self):
        return self.color

    class Meta:
        verbose_name = 'ColorAct'
        verbose_name_plural = 'ColorsAct'


class SpecialtyAct(models.Model):
    name = models.CharField(max_length=200)
    color = models.ForeignKey('ColorAct', on_delete=models.CASCADE,)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'SpecialtyAct'
        verbose_name_plural = 'SpecialtiesAct'


class ApproachAct(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'ApproachAct'
        verbose_name_plural = 'ApproachesAct'


class BubbleAct(models.Model):
    coordinate_approach = models.ForeignKey(
        'ApproachAct', null=True, on_delete=models.CASCADE)
    coordinate_speciality = models.ForeignKey(
        'SpecialtyAct', null=True, on_delete=models.CASCADE)
    color = models.ForeignKey('ColorAct', on_delete=models.CASCADE)
    list_of_people = models.TextField(
        null=True, blank=True)  # csv formatted email list


class UserProfileAct(models.Model):
    author_id = models.CharField(primary_key=True, default="", max_length=200)
    fullName = models.CharField(default="", max_length=100)
    scopusLink = models.URLField(default="", null=True)
    affiliation = models.TextField(null=True, blank=True)
    affiliationID = models.CharField(default="", max_length=200)
    approach = models.ManyToManyField('ApproachAct', blank=True)
    specialty = models.ManyToManyField('SpecialtyAct', blank=True)

    def __str__(self):
        return self.author_id

    class Meta:
        verbose_name = 'UserProfileAct'
        verbose_name_plural = 'UserProfilesAct'
