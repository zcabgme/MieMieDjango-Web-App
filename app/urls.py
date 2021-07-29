# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from django.conf.urls import url
from app import views

urlpatterns = [

    # The home page
    path('', views.index, name='home'),
    path('app', views.app, name='app'),
    path('sdg', views.sdg, name='sdg'),
    path('ihe', views.ihe, name='ihe'),
    path('universal_SVM', views.universal_SVM, name='universal_SVM'),
    path('universal_SVM_IHE', views.universal_SVM_IHE, name='universal_SVM_IHE'),
    path('sdgVisualisation', views.sdgVisualisation, name='sdgVisualisation'),
    path('iheVisualisation', views.iheVisualisation, name='iheVisualisation'),
    path('tableauVisualisation', views.tableauVisualisation, name='tableauVisualisation'),
    path('bubble_chart_act', views.bubble_chart_act, name='bubble_chart_act'),
    url(r'searchBubbleAct/(?P<pk>\d+)/(?P<pk_alt>\d+)/$', views.searchBubbleAct, name='searchBubbleAct'),
    
    # Matches any html file
    # re_path(r'^.*\.*', views.pages, name='pages'),


]
