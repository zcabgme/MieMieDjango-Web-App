# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from app import views

urlpatterns = [

    # The home page
    path('', views.index, name='home'),
    path('app', views.app, name='app'),
    path('sdg', views.sdg, name='sdg'),
    path('universal_SVM', views.universal_SVM, name='universal_SVM'),
    # Matches any html file
    # re_path(r'^.*\.*', views.pages, name='pages'),


]
