from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.postgres.fields import ArrayField
import json


class JSONField(models.TextField):
    """
    JSONField es un campo TextField que serializa/deserializa objetos JSON.
    Django snippet #1478
    Ejemplo:
        class Page(models.Model):
            data = JSONField(blank=True, null=True)
        page = Page.objects.get(pk=5)
        page.data = {'title': 'test', 'type': 3}
        page.save()
    """

    def to_python(self, value):
        if value == "":
            return None

        try:
            if isinstance(value, str):
                return json.loads(value)
        except ValueError:
            pass
        return value

    def from_db_value(self, value, *args):
        return self.to_python(value)

    def get_db_prep_save(self, value, *args, **kwargs):
        if value == "":
            return None
        if isinstance(value, dict):
            value = json.dumps(value, cls=DjangoJSONEncoder)
        return value


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


class Publication(models.Model):
    title = models.TextField(blank=True)
    data = models.JSONField(null=True, blank=True)
    assignedSDG = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f"/publication/{self.pk}"


class PyChart(models.Model):
    name = models.CharField(max_length=100, blank=True)
    picture = models.ImageField(
        null=True, blank=True, upload_to='charts/', default='')


class UserProfile(models.Model):
    email = models.EmailField(primary_key=True)
    fullName = models.CharField(default="", max_length=100)
    irisLink = models.URLField(default="", null=True)
    faculty = models.CharField(default="", max_length=200)
    status = models.ForeignKey('Status', on_delete=models.CASCADE)
    start_time = models.DateField(blank=True, null=True)
    approach = models.ManyToManyField('Approach', blank=True)
    specialty = models.ManyToManyField('Specialty', blank=True)

    def __str__(self):
        return self.email

    @property
    def get_year(self):
        return self.start_time.year

    class Meta:
        verbose_name = 'UserProfile'
        verbose_name_plural = 'UserProfiles'


class Color(models.Model):
    color = models.CharField(max_length=50)

    def __str__(self):
        return self.color

    class Meta:
        verbose_name = 'Color'
        verbose_name_plural = 'Colors'


class Approach(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Approach'
        verbose_name_plural = 'Approaches'


class Specialty(models.Model):
    name = models.CharField(max_length=200, null=True)
    color = models.ForeignKey('Color', on_delete=models.CASCADE,)

    def __str__(self):
        return self.name

    # class Meta:
    #     indexes = [
    #         models.Index(fields=['name']),
    #     ]


class Status(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Status'
        verbose_name_plural = 'Status'


class Bubble(models.Model):
    coordinate_approach = models.ForeignKey(
        'Approach', null=True, on_delete=models.CASCADE)
    coordinate_speciality = models.ForeignKey(
        'Specialty', null=True, on_delete=models.CASCADE)
    color = models.ForeignKey('Color', on_delete=models.CASCADE)
    list_of_people = models.TextField(
        null=True, blank=True)  # csv formatted email list


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
    approach = models.ManyToManyField('ApproachAct', blank=True)
    specialty = models.ManyToManyField('SpecialtyAct', blank=True)
    
    def __str__(self):
        return self.author_id

    class Meta:
        verbose_name = 'UserProfileAct'
        verbose_name_plural = 'UserProfilesAct'
