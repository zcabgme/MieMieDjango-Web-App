from django.contrib import admin
from .models import Module, Publication, UserProfile, Color, Approach, Specialty, Status

# Register your models here.
admin.site.register(Module)
admin.site.register(Publication)


admin.site.register(UserProfile)
admin.site.register(Color)
admin.site.register(Approach)
admin.site.register(Specialty)
admin.site.register(Status)
