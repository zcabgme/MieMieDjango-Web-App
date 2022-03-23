import configparser
from NLP.PREPROCESSING.module_preprocessor import ModuleCataloguePreprocessor
from NLP.PREPROCESSING.preprocessor import Preprocessor

from django.core import serializers
from django.shortcuts import render, redirect
from django.db.models.expressions import RawSQL
from .models import *
from django.views import View
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models.functions import Length
from django.views.decorators.csrf import csrf_exempt
from django.template.defaulttags import register
from .forms import BubbleChartAdd
from django.contrib.auth.decorators import login_required

import pyodbc
import json
import os
import math
import csv
import time
import sys
from io import BytesIO, StringIO
from colorsys import hsv_to_rgb
import matplotlib.pyplot as plt
from bson import json_util
import pymongo
import pickle
import base64
import numpy as np
import colorsys
import random
import matplotlib

matplotlib.use('Agg')

global_context = {}
global_query, global_mod_sdg_paginator, global_pub_sdg_paginator, global_ihe_paginator = None, None, None, None
prev_ihe_selector = 'Default'
num_of_lda_specialities = 0
svm_context = {"data": None, "Predicted": None, "form": {"Default Preprocessor": "selected", "UCL Module Catalogue Preprocessor": ""}}
Module_CSV_Data, Publication_CSV_Data, IHE_CSV_Data = None, None, None
lda_threshold, svm_threshold, paginator_limiter = 30, 30, 10


@login_required(login_url="/login/")
def index(request):
    """
        Returns the render for the Home page
    """

    return render(request, 'index.html', {"segment": "index"})


@login_required(login_url="/login/")
def app(request):
    global Module_CSV_Data, Publication_CSV_Data
    global global_context, global_query
    global global_mod_sdg_paginator, global_pub_sdg_paginator

    all_modules = Module.objects.all()
    all_publications = Publication.objects.all()

    context = {
        'mod': all_modules,
        'modules': None,
        'pub': all_publications,
        'publications': None,
        'len_mod': None,
        'len_pub': None,
        'segment': 'app'
    }

    url_string = ""

    if request.method == 'GET':
        if "q" in request.GET:

            query = request.GET.get('q')
            url_string = "q=" + str(query).replace(" ", "+")
            context['url_string'] = url_string + '&'

            if query is not None and query != '' and len(query) != 0 and query != global_query:
                context['pub'] = Publication.objects.filter(data__icontains=query).distinct()
                lookups = Q(Department_Name__icontains=query) | Q(Department_ID__icontains=query) | Q(
                    Module_Name__icontains=query) | Q(Module_ID__icontains=query) | Q(Faculty__icontains=query) | Q(
                    Module_Lead__icontains=query) | Q(Description__icontains=query)
                context['mod'] = Module.objects.filter(lookups).distinct()
                global_query = query
                global_pub_sdg_paginator, global_mod_sdg_paginator = Paginator(context['pub'], paginator_limiter), Paginator(context['mod'], paginator_limiter)

            else:
                Module_CSV_Data, Publication_CSV_Data = None, None
            url_string = "q=" + str(query).replace(" ", "+")

        else:
            global_mod_sdg_paginator, global_pub_sdg_paginator = Paginator(context['mod'], paginator_limiter), Paginator(context['pub'], paginator_limiter)
            global_query = None

        # Pagination
        context['modules'] = pagination_management(global_mod_sdg_paginator, request.GET.get('modPage'))
        context['publications'] = pagination_management(global_pub_sdg_paginator, request.GET.get('pubPage'))
        
        Module_CSV_Data, Publication_CSV_Data = context['mod'], context['pub']

        if url_string != "":
            url_string = url_string + "&"
        context['url_string'] = url_string

        context['len_mod'] = global_mod_sdg_paginator.count
        context['len_pub'] = global_pub_sdg_paginator.count

    global_context = context
    return render(request, 'search_engine.html', context)


def pagination_management(paginator, selected_page):
    """
        Manages pagination for data display
        For: search engine, SDG data display, IHE data display, Bubble Chart author display
    """
    
    try:
        objects = paginator.page(selected_page)
    except PageNotAnInteger:
        objects = paginator.page(1)
    except EmptyPage:
        objects = paginator.page(paginator.num_pages)
    return objects

@login_required(login_url="/login/")
def bubble_chart_act(request):
    """
        Returns the render for the Bubble Chart page
    """

    # Gather and set the approaches and specialities
    approach_list = ApproachAct.objects.all().values_list('id', flat=True)
    speciality_list = SpecialtyAct.objects.all().values_list('id', flat=True)
    speciality_list = speciality_list.order_by('id')
    bubbles = BubbleAct.objects.all()



    approach_dict = {int(i.id): i.name for i in ApproachAct.objects.all()}
    speciality_dict = {int(i.id): i for i in SpecialtyAct.objects.all()}

    
    # Calculate the highest number of authors currently in a bubble in order to determine sizes
    CONST_SCALE_MAX, SIZE_MIN = 25, 9
    curr_max = 0
    for i in bubbles:
        if i.list_of_people.count(',') + 1 > curr_max:
            curr_max = i.list_of_people.count(',') + 1

    # Make a dict with the bubbles by coordinate and their scaled sizes
    bubble_dict = {}
    for i in approach_list:
        bubble_dict[approach_dict[i]] = {}
        for j in speciality_list:
            try:
                # Try: check if a bubble exists, calculate its size and populate the dict
                bubble_obj = bubbles.get(coordinate_approach=int(i), coordinate_speciality=int(j))
                size = (((bubble_obj.list_of_people.count(',') + 1) / curr_max) * (CONST_SCALE_MAX - SIZE_MIN)) + SIZE_MIN
                bubble_dict[approach_dict[i]][int(j)] = [bubble_obj, size]
            except:
                # Except: bubble doesn't exist, there is nothing in that coordinate
                bubble_dict[approach_dict[i]][int(j)] = None
    


    # Generate final context
    context = {
        'approach_list': approach_list,
        'speciality_list': speciality_list,
        'speciality_dict': speciality_dict,
        'approach_dict': approach_dict,
        'bubbles': bubble_dict,
        'segment': 'bubble_chart'
    }

    return render(request, 'bubble_chart.html', context)


def searchBubbleAct(request, pk=None, pk_alt=None):
    """
        Returns the render for the Search Bubble page (when user clicks on a bubble)
    """

    form = {"ALL": "selected", "UCL Authors": "unselected", "OTHER Authors": "unselected"}
    ucl_id = '60022148'

    # Get the bubble the user has clicked on and get the list of emails
    obj = BubbleAct.objects.get(coordinate_approach=pk, coordinate_speciality=pk_alt)
    list_of_emails = obj.list_of_people.split(',')
    entry_list = []

    if request.method == 'GET':
        # Get list of all authors and the user's selection of which ones to return
        people = UserProfileAct.objects.all()
        query = request.GET.get('author_selection')

        # Find and generate the entry_list based on user's choice of authors
        if query == 'UCL Authors':
            form['UCL Authors'] = "selected"
            form['OTHER Authors'] = "unselected"
            form['ALL'] = "unselected"
            ok = people.exclude(affiliationID="")
            for i in ok:
                if i != "null":
                    if ucl_id in i.affiliationID and i.author_id in list_of_emails:
                        entry_list.append(i)

        elif query == 'OTHER Authors':
            form['OTHER Authors'] = "selected"
            form['UCL Authors'] = "unselected"
            form['ALL'] = "unselected"
            ok = people.exclude(affiliationID="")
            for i in ok:
                if i != "null":
                    if ucl_id not in i.affiliationID and i.author_id in list_of_emails:
                        entry_list.append(i)

        elif query == 'ALL':
            form['OTHER Authors'] = "unselected"
            form['UCL Authors'] = "unselected"
            form['ALL'] = "selected"
            ok = people.exclude(affiliationID="")
            for i in ok:
                if i != "null" and i.author_id in list_of_emails:
                    entry_list.append(i)

        # Pagination
        authors = pagination_management(Paginator(entry_list, 10), request.GET.get('page'))

    url_string = 'csrfmiddlewaretoken=' + str(request.GET.get('csrfmiddlewaretoken')) + '&author_selection=' + str(
        request.GET.get('author_selection')).replace(" ", "+") + "&"

    num_of_people = len(entry_list)
    app_spec = [ApproachAct.objects.get(id=pk), SpecialtyAct.objects.get(id=pk_alt), pk, pk_alt]

    return render(request, 'search_bubble.html',
                  {"form": form, "entry_list": authors, "assignments": app_spec, "num_of_people": num_of_people,
                   "url_string": url_string})

@login_required(login_url="/login/")
def manual_add(request):
    """
        Returns the render for the Manual Add page
    """

    # Gets the lists of all approaches and specialities with the manual add form
    approach_list = ApproachAct.objects.all()
    specialty_list = SpecialtyAct.objects.all()
    form = BubbleChartAdd()

    # Selectors for approach and speciality
    approach_select = {"Default": "unselected"}
    for i in approach_list:
        approach_select[i] = "unselected"

    speciality_select = {"Default": "unselected"}
    for i in specialty_list:
        speciality_select[i] = "unselected"

    if request.method == "POST":
        # Once user has clicked submit, receive the submitted form
        form = BubbleChartAdd(request.POST or None)

        if form.is_valid():
            # Save to database if it's valid
            form.save()
        else:
            # Else store what they entered to autofill the form and return them to the page
            saved_data = {
                "author_id": request.POST['author_id'],
                "fullName": request.POST['fullName'],
                "affiliation": request.POST['affiliation'],
                "affiliationID": request.POST['affiliationID'],
                "approach": request.POST['approach'],
                "specialty": request.POST['specialty'],
                "form": form
            }
            messages.success(request, ("There was an error in your form! Please try again."))
            return render(request, 'manual_add.html', saved_data)

        messages.success(request, ("Your form has been submitted successfully!"))
        return redirect('manual_add')

    else:
        # Base case if the user has just come to the page
        return render(request, 'manual_add.html', {"form": form, "approach_select": approach_select, "speciality_select": speciality_select})


@login_required(login_url="/login/")
def iheVisualisation(request):
    """
        Returns the render for the IHE Visualisation page
    """

    # Get the visualisation data from MongoDB
    client = pymongo.MongoClient(get_details('MONGO_DB', 'client'))
    col = client.Scopus.Visualisations
    data = list(col.find())[0]

    # Generate the context for IHE specific PyLDAvis and t-SNE visualisations
    context = {
        "pylda": data['PyLDA_ihe'],
        "tsne": data['TSNE_ihe'],
        "segment": "iheVisualisation"
    }
    client.close()
    return render(request, "ihe_model_vis.html", context)

@login_required(login_url="/login/")
def selectSDGorFaculty(request):
    """
        Returns the render for the SDG selection page
    """

    return render(request, "SdgFacultyIndex.html")


@login_required(login_url="/login/")
def sdgVisualisation(request):
    """
        Returns the render for the SDG Visualisation page
    """

    # Get the visualisation data from MongoDB
    client = pymongo.MongoClient('mongodb+srv://yzyucl:qq8588903@miemie.jbizr.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')
    col = client.Scopus.Visualisations
    data = list(col.find())[1]

    # Generate the context for SDG specific PyLDAvis and t-SNE visualisations
    context = {
        "pylda": data['PyLDA_sdg'],
        "tsne": data['TSNE_sdg'],
        "segment": "sdgVisualisation"
    }
    client.close()
    return render(request, "sdg_model_vis.html", context)


@login_required(login_url="/login/")
def sdg(request):
    """
        Returns the render for the SDG Tables page
    """

    global global_context
    global global_query
    global global_mod_sdg_paginator, global_pub_sdg_paginator

    # Generate base context
    context = {
        'mod': Module.objects.all(),
        'pub': Publication.objects.all(),
        'modules': None,
        'publications': None,
        'len_mod': None,
        'len_pub': None,
        'segment': 'sdg'
    }

    if request.method == 'GET':
        if "q" in request.GET:
            # If the user has entered something to search
            query = request.GET.get('q')

            if query is not None and query != '' and len(query) != 0 and query != global_query:
                # If the search is valid and different to the previous search, get new results
                context['pub'] = Publication.objects.filter(data__icontains=query).distinct()
                lookups = Q(Department_Name__icontains=query) | Q(Department_ID__icontains=query) | Q(
                    Module_Name__icontains=query) | Q(Module_ID__icontains=query) | Q(Faculty__icontains=query) | Q(
                    Module_Lead__icontains=query) | Q(Description__icontains=query)
                context['mod'] = Module.objects.filter(lookups).distinct()
                # Set the global query and paginator to reflect the new search
                global_query = query
                global_pub_sdg_paginator, global_mod_sdg_paginator = Paginator(context['pub'], 10), Paginator(
                    context['mod'], 10)
            url_string = "q=" + str(query).replace(" ", "+")

        else:
            # Base case if the user has just come to the page
            global_pub_sdg_paginator, global_mod_sdg_paginator = Paginator(context['pub'], 10), Paginator(context['mod'], 10)
            global_query = None

        # Pagination
        context['modules'] = pagination_management(global_mod_sdg_paginator, request.GET.get('modPage'))
        context['publications'] = pagination_management(global_pub_sdg_paginator, request.GET.get('pubPage'))

        context['len_mod'] = global_mod_sdg_paginator.count
        context['len_pub'] = global_pub_sdg_paginator.count

    return render(request, 'sdg_tables.html', context)


@login_required(login_url="/login/")
def module(request, pk):
    """
        Returns the render for the Module page
    """
    # Get the module specified by the user if it exists to display information about it
    try:
        module = Module.objects.get(id=pk)
    except Module.DoesNotExist:
        raise ("Module does not exist")
    return render(request, 'module.html', {'mod': module})

@login_required(login_url="/login/")
def SDG1(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'SDG1.html')

@login_required(login_url="/login/")
def SDG2(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'SDG2.html')

@login_required(login_url="/login/")
def SDG3(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'SDG3.html')

@login_required(login_url="/login/")
def SDG4(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'SDG4.html')

@login_required(login_url="/login/")
def SDG5(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'SDG5.html')

@login_required(login_url="/login/")
def SDG6(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'SDG6.html')

@login_required(login_url="/login/")
def SDG7(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'SDG7.html')

@login_required(login_url="/login/")
def SDG8(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'SDG8.html')

@login_required(login_url="/login/")
def SDG9(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'SDG9.html')

@login_required(login_url="/login/")
def SDG10(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'SDG10.html')

@login_required(login_url="/login/")
def SDG11(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'SDG11.html')

@login_required(login_url="/login/")
def SDG12(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'SDG12.html')

@login_required(login_url="/login/")
def SDG13(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'SDG13.html')

@login_required(login_url="/login/")
def SDG14(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'SDG14.html')

@login_required(login_url="/login/")
def SDG15(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'SDG15.html')

@login_required(login_url="/login/")
def SDG16(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'SDG16.html')

@login_required(login_url="/login/")
def SDG17(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'SDG17.html')

@login_required(login_url="/login/")
def Faculty1(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'Faculty1.html')

@login_required(login_url="/login/")
def Faculty2(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'Faculty2.html')

@login_required(login_url="/login/")
def Faculty3(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'Faculty3.html')

@login_required(login_url="/login/")
def Faculty4(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'Faculty4.html')

@login_required(login_url="/login/")
def Faculty5(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'Faculty5.html')

@login_required(login_url="/login/")
def Faculty6(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'Faculty6.html')

@login_required(login_url="/login/")
def Faculty7(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'Faculty7.html')

@login_required(login_url="/login/")
def Faculty8(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'Faculty8.html')

@login_required(login_url="/login/")
def Faculty9(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'Faculty9.html')

@login_required(login_url="/login/")
def Faculty10(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'Faculty10.html')

@login_required(login_url="/login/")
def Faculty11(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'Faculty11.html')


@login_required(login_url="/login/")
def HA1(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'HA1.html')

@login_required(login_url="/login/")
def HaIndex(request):
    """
        Returns the render for the sdg graph
    """
    
    return render(request, 'HaIndex.html')

@login_required(login_url="/login/")
def viewInformationSDG(request):
    """
        Returns the render for the sdg table

    """
    connection = getSQL_connection()
    cursor = connection.cursor()
    query = """SELECT testmodassign.SDG, COUNT(DISTINCT testmodassign.Module_ID), SUM(studentspermodule.NumberOfStudents)
                FROM testmodassign
                INNER JOIN studentspermodule ON testmodassign.Module_ID=studentspermodule.ModuleID 
                GROUP BY testmodassign.SDG;"""
    result = cursor.execute(query)
    sdgs = result.fetchall()
    context = list()
    for sdg in sdgs:
         context.append({"Faculties": sdgs[0],
            "Module Code": sdgs[1],
            "Number of Students":sdgs[2] })

    return render(request, 'viewInformationSDG.html', {"context": context})

@login_required(login_url="/login/")
def viewInformationFaculty(request):
    """
        Returns the render for the faculty table

    """
    #connection = getSQL_connection()


    #context = {"Faculties": ,
            #"Modules": ,
            #"Number of Students": }
    return render(request, 'viewInformationFaculty.html')

@login_required(login_url="/login/")
def viewInformationHA(request):
    """
        Returns the render for the ha table

    """
    #connection = getSQL_connection()


    #context = {"Faculties": ,
            #"Modules": ,
            #"Number of Students": }
    return render(request, 'viewInformationHA.html')



@login_required(login_url="/login/")
def publication(request, pk):
    """
        Returns the render for the Publication page
    """
    # Get the publication specified by the user if it exists to display information about it
    try:
        publication = Publication.objects.get(id=pk)
    except Publication.DoesNotExist:
        raise ("Publication does not exist")
    return render(request, 'publication.html', {'pub': publication})


@login_required(login_url="/login/")
def export_modules_csv(request):
    """
        Export currently displayed / searched modules on the Search Engine web-page
        Generates CSV file with relevant fields containing module metadata
    """

    global Module_CSV_Data, global_context
    response = HttpResponse(content_type='text/csv')

    if not Module_CSV_Data:
        messages.success(request, ("No modules to export! Please try again."))
        return render(request, 'index.html', global_context)

    response['Content-Disposition'] = 'attachment; filename="modules.csv"'

    try:
        writer = csv.writer(response)
        writer.writerow(["Department_Name", "Department_ID", "Module_Name", "Module_ID",
                         "Faculty", "Credit_Value", "Module_Lead", "Catalogue_Link", "Description"])
        modules = Module_CSV_Data.values_list("Department_Name", "Department_ID", "Module_Name",
                                              "Module_ID", "Faculty", "Credit_Value", "Module_Lead", "Catalogue_Link",
                                              "Description")
        for module in modules:
            writer.writerow(module)
    except:
        messages.success(request, ("No modules to export! Please try again."))
        return render(request, 'index.html', global_context)

    return response


@login_required(login_url="/login/")
def export_publications_csv(request):
    """
        Export currently displayed / searched publications on the Search Engine web-page
        Separates UCL & non-UCL authors into split columns
        Generates CSV file with relevant fields containing publication metadata
    """

    global Publication_CSV_Data, global_context

    response = HttpResponse(content_type='text/csv')

    if not Publication_CSV_Data:
        messages.success(request, ("No publications to export! Please try again."))
        return render(request, 'index.html', global_context)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="publications.csv"'

    try:
        writer = csv.writer(response)
        writer.writerow(
            ["Title", "EID", "DOI", "Year", "Source", "Volume", "Issue", "Page-Start", "Page-End", "Cited By",
             "Link", "Abstract", "Author Keywords", "Index Keywords", "Dcoument Type", "Publication Stage",
             "Open Access", "Subject Areas", "UCL Authors Data", "Other Authors Data"])
    except:
        messages.success(request, ("No publications to export! Please try again."))
        return render(request, 'index.html', global_context)

    publications = Publication_CSV_Data.values_list("data")
    for paper in publications:
        detail = json.dumps(paper)
        all_contents = json.loads(detail)[0]
        title = all_contents['Title']
        EID = all_contents['EID']
        DOI = all_contents['DOI']
        Year = all_contents['Year']
        Source = all_contents['Source']
        Volume = all_contents['Volume']
        Issue = all_contents['Issue']
        PageStart = all_contents['PageStart']
        PageEnd = all_contents['PageEnd']
        CitedBy = all_contents['CitedBy']
        Link = all_contents['Link']
        Abstract = all_contents['Abstract']
        AuthorKeywords = all_contents['AuthorKeywords']
        if AuthorKeywords: AuthorKeywords = ','.join(AuthorKeywords)
        IndexKeywords = all_contents['IndexKeywords']
        if IndexKeywords: IndexKeywords = ','.join(IndexKeywords)
        DocumentType = all_contents['DocumentType']
        PublicationStage = all_contents['PublicationStage']
        OpenAccess = all_contents['OpenAccess']
        SubjectAreas = all_contents['SubjectAreas']
        temp = []
        if SubjectAreas:
            for area in SubjectAreas:
                temp.append(area[0])
        SubjectAreas = ','.join(temp)
        AuthorData = all_contents['AuthorData']
        UCLAuthorsData, OtherAuthorsData = [], []
        if AuthorData:
            for id_ in AuthorData:
                name = AuthorData[id_]['Name']
                affiliationID = AuthorData[id_]['AffiliationID']
                affiliationName = AuthorData[id_]['AffiliationName']
                if affiliationID == "60022148":
                    if affiliationName:
                        UCLAuthorsData.append(name + "(" + affiliationName + ")")
                    else:
                        UCLAuthorsData.append(name)
                else:
                    if name and not affiliationName:
                        OtherAuthorsData.append(','.join([name, ""]))
                    if not name and not affiliationName:
                        OtherAuthorsData.append("")
                    if name and affiliationName:
                        OtherAuthorsData.append(name + "(" + affiliationName + ")")

        UCLAuthorsData = ','.join(UCLAuthorsData)
        OtherAuthorsData = ','.join(OtherAuthorsData)

        writer.writerow(
            [title, EID, DOI, Year, Source, Volume, Issue, PageStart, PageEnd, CitedBy, Link, Abstract, AuthorKeywords,
             IndexKeywords, DocumentType, PublicationStage, OpenAccess, SubjectAreas, UCLAuthorsData, OtherAuthorsData])

    return response


def unpickle_svm_model(filename):
    """
        Returns unpickled SVM model for SVM Universal web-pages (SDG + IHE)
    """

    with open(filename, "rb") as input_file:
        return pickle.load(input_file)


def make_SVM_prediction(text, processor: str) -> list:
    """
        Apply the SVM model on unseen text (for SDG's) using selected preprocessor
    """

    svm = unpickle_svm_model("NLP/SVM/SDG/model.pkl")
    preprocessor = ModuleCataloguePreprocessor() if processor == "module" else Preprocessor()
    predictions = svm.make_text_predictions(text, preprocessor)
    return predictions


def make_SVM_IHE_prediction(text) -> list:
    """
        Apply the SVM model on unseen text (for IHE's)
    """

    svm = unpickle_svm_model("NLP/SVM/IHE/model.pkl")
    predictions = svm.make_text_predictions(text, Preprocessor())
    return predictions


def check_svm_processor(request, form: dict) -> dict:
    """
        Process the drop-down select for preprocessor options (for the SDG SVM Universal web-page)
    """

    form['Default Preprocessor'] = "checked" if request.GET.get('sorting') == "Default Preprocessor" else ""
    form['UCL Module Catalogue Preprocessor'] = "checked" if request.GET.get(
        'sorting') == "UCL Module Catalogue Preprocessor" else ""
    return form


def drawDonutChart(results, labels: list):
    """
        Dynamically generate a donut chart for both SDG and IHE predictions from the universal SVM
        Encodes the image in base64, decoded within HTML web-page using the safe pipe operator '|'
    """

    fig, ax = plt.subplots(figsize=(10, 7), subplot_kw=dict(aspect="equal"))
    wedges, texts = ax.pie(results, wedgeprops=dict(width=0.5), startangle=-40)
    bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
    kw = dict(arrowprops=dict(arrowstyle="-"), bbox=bbox_props, zorder=0, va="center")

    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1) / 2. + p.theta1
        x, y = np.cos(np.deg2rad(ang)), np.sin(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        ax.annotate(labels[i], xy=(x, y), xytext=(1.35 * np.sign(x), 1.4 * y), horizontalalignment=horizontalalignment,
                    **kw)

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')
    return graphic


def truncate(n: float, decimals: int = 0) -> float:
    """
        Support function to truncate any float value to a specified decimal points
    """

    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier


@login_required(login_url="/login/")
def universal_SVM(request):
    """
        Leverages SVM model to predict SDG category for unseen documents or text
    """

    global svm_context
    sdg_list = ["SDG " + str(i) for i in range(1, 18)]
    sdg_list.append("Misc")
    svm_context['segment'] = 'universal_SVM'

    if request.method == "GET":
        svm_context['form'] = check_svm_processor(request, svm_context['form'])
        query = request.GET.get('box')
        preprocessor = "module" if svm_context['form']['UCL Module Catalogue Preprocessor'] == "checked" else "default"
        if query and query != "":
            prediction = make_SVM_prediction(query, processor=preprocessor)[0]
            prediction_list = prediction.tolist()
            results, predicted_ = [], []
            for i in range(len(prediction_list)):
                temp = truncate(prediction_list[i] * 100, 1)
                results.append(temp)
                if temp >= svm_threshold:
                    predicted_.append(str(i + 1))
            svm_context["data"] = results
            svm_context["Predicted"] = ','.join(predicted_)
            svm_context["graphic"] = drawDonutChart(results, sdg_list)
            return render(request, 'svm_universal.html', svm_context)
        else:
            return render(request, 'svm_universal.html',
                          {"data": None, "Predicted": None, "form": svm_context['form'], "graphic": None,
                           "segment": "universal_SVM"})
    return render(request, 'svm_universal.html', svm_context)


@login_required(login_url="/login/")
def universal_SVM_IHE(request):
    """
        Leverages SVM model to predict IHE category for unseen documents or text
    """

    svm_context = {}
    svm_context['segment'] = 'IHE'

    l = ApproachAct.objects.all().count()
    ihe_list = ["IHE " + str(i + 1) for i in range(l)]

    if request.method == "GET":
        query = request.GET.get('box')

        if query and query != "":
            prediction = make_SVM_IHE_prediction(query)[0]
            prediction_list = prediction.tolist()
            results, predicted_ = [], []
            for i in range(len(prediction_list)):
                temp = truncate(prediction_list[i] * 100, 1)
                results.append(temp)
                if temp >= svm_threshold:
                    predicted_.append(str(i + 1))
            svm_context["data"] = results
            svm_context["Predicted"] = ','.join(predicted_)
            svm_context["graphic"] = drawDonutChart(results, ihe_list)

            return render(request, 'ihe_svm_universal.html', svm_context)
        else:
            return render(request, 'ihe_svm_universal.html',
                          {"data": None, "Predicted": None, "graphic": None, "segment": "IHE"})
    return render(request, 'ihe_svm_universal.html', svm_context)


def getCheckBoxState_ihe(request, form, number_of_ihe):
    """
        Process the current state of IHE prediction filter
        (support function for the IHE web-page)
    """

    for i in range(1, number_of_ihe + 1):
        form[str(i)] = "selected" if request.GET.get('prediction') == str(i) else "unselected"
    return form


@login_required(login_url="/login/")
def export_ihe_csv(request):
    """
        Export authors based on the current IHE viewing page
        Results in a CSV file with columns: Name, Prediction, DOI, Abstract
    """

    global IHE_CSV_Data

    if not IHE_CSV_Data:
        messages.success(request, ("No IHE publications to export! Please try again."))
        return render(request, 'ihe.html', {})

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="ihe_publications.csv"'

    try:
        writer = csv.writer(response)
        writer.writerow(["Name", "Prediction", "DOI", "Abstract"])
    except:
        messages.success(request, ("No IHE publications to export! Please try again."))
        return render(request, 'ihe.html', {})

    for paper in IHE_CSV_Data:
        first = True
        author_data = paper.data['AuthorData']
        Prediction = paper.assignedSDG['IHE_Prediction']
        DOI = paper.data['DOI']
        Abstract = paper.data['Abstract']

        for author_id, values in author_data.items():
            if first:
                writer.writerow([values['Name'], Prediction, DOI, Abstract])
                first = False
            else:
                writer.writerow([values['Name'], "", "", ""])

    return response


def get_columns() -> dict:
    columns = SpecialtyAct.objects.all()
    result = {}

    for i in columns:
        result[i.id] = str(i)

    return result


@login_required(login_url="/login/")
def ihe(request):
    """
       IHE assignments display page
       Allows for search and filtering by IHE assignment 
    """

    global global_query, global_ihe_paginator, IHE_CSV_Data, prev_ihe_selector, num_of_lda_specialities
    number_of_LDA_specialities = SpecialtyAct.objects.all().filter(methodology='LDA').count()
    
    if 'prediction' not in request.GET:
        prev_ihe_selector = 'Default'


    if num_of_lda_specialities == 0:
        num_of_lda_specialities = SpecialtyAct.objects.all().filter(methodology='LDA').count()


    form = {"Default": "unselected"}

    lookup = get_columns()

    number_of_ihe = len(lookup)

    for i in range(1, number_of_ihe + 1):
        form[str(i)] = 'unselected'

    context = {
        'pub': Publication.objects.all(),
        'len_pub': Publication.objects.count(),
        'form': form,
        'ihe_lookup': lookup,
        'number_of_LDA_specialities': number_of_LDA_specialities,
        'segment': 'ihe',
        'table_select': ''
    }

    url_string = ""

    if request.method == 'GET':
        if "q" in request.GET:

            query = request.GET.get('q')
            context['form'] = getCheckBoxState_ihe(request, form, number_of_ihe)

            if query is not None and query != '' and len(query) != 0 and query != global_query:
                context['pub'] = context['pub'].filter(data__icontains=query).distinct()
                global_query = query
                global_ihe_paginator = Paginator(context['pub'], paginator_limiter)

            url_string = url_string + "q=" + str(query).replace(" ", "+")

        else:
            global_ihe_paginator = Paginator(context['pub'], paginator_limiter)
            global_query = None

        for key, val in form.items():
            if val == "selected" and key != "Default" and key != prev_ihe_selector:
                k = int(key)
                if k <= num_of_lda_specialities:
                    context['table_select'] = 'LDA'
                    context['pub'] = context['pub'].filter(assignedSDG__IHE_Prediction__iregex=r'^.*{0}.*$'.format(key))

                    for publ in context['pub']:
                        if len(publ.assignedSDG['IHE_Prediction']) > 1:
                            predictions = publ.assignedSDG['IHE_Prediction'].split(',')
                            if key not in predictions:
                                context['pub'] = context['pub'].exclude(pk=publ.pk)
                else:
                    context['table_select'] = 'String'
                    context['pub'] = context['pub'].filter(assignedSDG__IHE_String_Speciality_Prediction__iregex=r'^.*{0}.*$'.format(key))

                    for publ in context['pub']:
                        if len(publ.assignedSDG['IHE_String_Speciality_Prediction']) > 1:
                            predictions = publ.assignedSDG['IHE_String_Speciality_Prediction'].split(',')
                            if key not in predictions:
                                context['pub'] = context['pub'].exclude(pk=publ.pk)
                
                prev_ihe_selector = key
                global_ihe_paginator = Paginator(context['pub'], paginator_limiter)
                
            if val == "selected" and key != "Default":
                url_string = url_string + "&prediction=" + str(request.GET.get('prediction'))
            
            context['table_select'] = 'Default' if prev_ihe_selector == 'Default' else 'LDA' if int(prev_ihe_selector) <= num_of_lda_specialities else 'String'
            
        # Pagination
        context['ihes'] = pagination_management(global_ihe_paginator, request.GET.get('ihePage'))

        IHE_CSV_Data = context['pub']

        if url_string != "": url_string = url_string + "&"
        context['url_string'] = url_string
        context['len_pub'] = global_ihe_paginator.count

    return render(request, 'ihe.html', context)


def get_details(field, detail):
    """
        Config parser
        Reads config.ini file, returns data from an appropriate field and detail
    """

    config = configparser.ConfigParser()
    config.read("config.ini")
    return config[field][detail]


def getSQL_connection():
    """
        Returns MySQL connection object for data retrieval
    """
    myConnection = pyodbc.connect('DRIVER=/usr/local/mysql-connector-odbc-8.0.28-macos11-x86-64bit/lib/libmyodbc8a.so;SERVER=127.0.0.1;DATABASE=mysqlmiemie;UID=root;PWD=Gomeni73;')

    return myConnection


@login_required(login_url="/login/")
def tableauVisualisation(request):
    """
        Tableau alternative page
        Draws 3 bubble charts based on MySQL database data using embedded JavaScript
    """

    curr = getSQL_connection().cursor()
    checkboxes = {'value1': '', 'value2': '', 'value3': ''}

    hue = random.randrange(0, 360)
    saturation = random.uniform(0, 1)
    luminance = random.uniform(30, 70)
    rgb = colorsys.hsv_to_rgb(hue, saturation, luminance)

    if request.method == 'GET':
        query = request.GET.get('exampleRadios')

        if query == "sdg_bubble":
            query = """
                SELECT testmodassign.SDG, COUNT(DISTINCT testmodassign.Module_ID), SUM(studentspermodule.NumberOfStudents)
                FROM testmodassign
                INNER JOIN studentspermodule ON testmodassign.Module_ID=studentspermodule.ModuleID 
                GROUP BY testmodassign.SDG;"""
            curr.execute(query)
            sdg_bubbles = curr.fetchall()  # (assigned sdg, module id, number of students)
            module_bubble_list = list()
            for sdg in sdg_bubbles:
                module_bubble_list.append({
                    'SDG': str(sdg[0]),
                    'Number_Students': sdg[2],
                    'Number_Modules': sdg[1]
                })
            colour_dict = {}
            for sdg in module_bubble_list:
                h, s, l = random.random(), 0.5 + random.random() / 2.0, 0.4 + random.random() / 5.0
                r, g, b = [int(256 * i) for i in colorsys.hls_to_rgb(h, l, s)]
                rgb = (round(r), round(g), round(b))
                colour_dict[str(sdg['SDG'])] = '#%02x%02x%02x' % rgb


            checkboxes['value1'] = 'checked'
            checkboxes['value2'] = ''
            checkboxes['value3'] = ''
            return render(request, 'tableau_vis.html',
                          {'selector': 'modules', 'bubble_list': module_bubble_list, 'colours': colour_dict, 'radios': checkboxes,
                           'segment': tableauVisualisation})

        if query == "department_sdg_bubble":
            query = """
                SELECT moduledata.Department_Name, COUNT(testmodassign.Module_ID), COUNT(DISTINCT(testmodassign.SDG)), SUM(studentspermodule.NumberOfStudents) FROM moduledata
                INNER JOIN testmodassign ON moduledata.Module_ID = testmodassign.Module_ID
                INNER JOIN studentspermodule ON moduledata.Module_ID = studentspermodule.ModuleID
                GROUP BY moduledata.Department_Name;"""
            curr.execute(query)
            department_bubble_sdg = curr.fetchall()  # (department name, num of modules, sdg coverage, num of students)
            department_bubble_list = list()
            for departments in department_bubble_sdg:
                department_bubble_list.append({
                    'Department': departments[0],
                    'Number_Modules': departments[1],
                    'SDG_Count': departments[2],
                    'Number_Students': departments[3]
                })

            colour_dict = {}
            for departments in department_bubble_list:
                h, s, l = random.random(), 0.5 + random.random() / 2.0, 0.4 + random.random() / 5.0
                r, g, b = [int(256 * i) for i in colorsys.hls_to_rgb(h, l, s)]
                rgb = (round(r), round(g), round(b))
                colour_dict[str(departments['Department'])
                ] = '#%02x%02x%02x' % rgb

            checkboxes['value1'] = ''
            checkboxes['value2'] = 'checked'
            checkboxes['value3'] = ''
            return render(request, 'tableau_vis.html',
                          {'selector': 'departments', 'bubble_list': department_bubble_list, 'colours': colour_dict,
                           'radios': checkboxes, 'segment': tableauVisualisation})

        if query == "faculty_sdg_bubble":
            query = """
                SELECT moduledata.Faculty, SUM(studentspermodule.NumberOfStudents), COUNT(testmodassign.Module_ID), COUNT(DISTINCT(testmodassign.SDG)) FROM studentspermodule
                INNER JOIN moduledata ON studentspermodule.ModuleID = moduledata.Module_ID
                INNER JOIN testmodassign ON studentspermodule.ModuleID = testmodassign.Module_ID
                GROUP BY moduledata.Faculty;"""
            curr.execute(query)
            faculty_bubble_sdg = curr.fetchall()
            faculty_bubble_list = list()
            for faculties in faculty_bubble_sdg:
                faculty_bubble_list.append({
                    'Faculty': faculties[0],
                    'Number_Modules': faculties[2],
                    'SDG_Count': faculties[3],
                    'Number_Students': faculties[1]
                })

            colour_dict = {}
            for faculties in faculty_bubble_list:
                h, s, l = random.random(), 0.5 + random.random() / 2.0, 0.4 + random.random() / 5.0
                r, g, b = [int(256 * i) for i in colorsys.hls_to_rgb(h, l, s)]
                rgb = (round(r), round(g), round(b))
                colour_dict[str(faculties['Faculty'])] = '#%02x%02x%02x' % rgb

            checkboxes['value1'] = ''
            checkboxes['value2'] = ''
            checkboxes['value3'] = 'checked'
            return render(request, 'tableau_vis.html',
                          {'selector': 'faculties', 'bubble_list': faculty_bubble_list, 'colours': colour_dict,
                           'radios': checkboxes, 'segment': tableauVisualisation})

    return render(request, 'tableau_vis.html', {})

@login_required(login_url="/login/")
def tableauVisualisationHA(request):
    curr = getSQL_connection().cursor()
    checkboxes = {'value1': '', 'value2': '', 'value3': ''}

    hue = random.randrange(0, 360)
    saturation = random.uniform(0, 1)
    luminance = random.uniform(30, 70)
    rgb = colorsys.hsv_to_rgb(hue, saturation, luminance)

    if request.method == 'GET':
        query = request.GET.get('exampleRadios')

        if query == "sdg_bubble":
            query = """
                SELECT testmodassign.SDG, COUNT(DISTINCT testmodassign.Module_ID), SUM(studentspermodule.NumberOfStudents)
                FROM [dbo].[testmodassign]
                INNER JOIN studentspermodule ON testmodmssign.Module_ID=studentspermodule.ModuleID 
                GROUP BY testmodassign.SDG;"""
            curr.execute(query)
            sdg_bubbles = curr.fetchall()  # (assigned sdg, module id, number of students)
            module_bubble_list = list()
            for sdg in sdg_bubbles:
                module_bubble_list.append({
                    'SDG': str(sdg[0]),
                    'Number_Students': sdg[2],
                    'Number_Modules': sdg[1]
                })

            checkboxes['value1'] = 'checked'
            checkboxes['value2'] = ''
            checkboxes['value3'] = ''
            return render(request, 'tableau_vis_ha.html',
                          {'selector': 'modules', 'bubble_list': module_bubble_list, 'radios': checkboxes,
                           'segment': tableauVisualisation})

        if query == "department_sdg_bubble":
            query = """
                SELECT ModuleData.Department_Name, COUNT(TestModAssign.Module_ID), COUNT(DISTINCT(TestModAssign.SDG)), SUM(StudentsPerModule.NumberOfStudents) FROM [dbo].[ModuleData]
                INNER JOIN TestModAssign ON ModuleData.Module_ID = TestModAssign.Module_ID
                INNER JOIN StudentsPerModule ON ModuleData.Module_ID = StudentsPerModule.ModuleID
                GROUP BY ModuleData.Department_Name;"""
            curr.execute(query)
            department_bubble_sdg = curr.fetchall()  # (department name, num of modules, sdg coverage, num of students)
            department_bubble_list = list()
            for departments in department_bubble_sdg:
                department_bubble_list.append({
                    'Department': departments[0],
                    'Number_Modules': departments[1],
                    'SDG_Count': departments[2],
                    'Number_Students': departments[3]
                })

            colour_dict = {}
            for departments in department_bubble_list:
                h, s, l = random.random(), 0.5 + random.random() / 2.0, 0.4 + random.random() / 5.0
                r, g, b = [int(256 * i) for i in colorsys.hls_to_rgb(h, l, s)]
                rgb = (round(r), round(g), round(b))
                colour_dict[str(departments['Department'])
                ] = '#%02x%02x%02x' % rgb

            checkboxes['value1'] = ''
            checkboxes['value2'] = 'checked'
            checkboxes['value3'] = ''
            return render(request, 'tableau_vis_ha.html',
                          {'selector': 'departments', 'bubble_list': department_bubble_list, 'colours': colour_dict,
                           'radios': checkboxes, 'segment': tableauVisualisation})

        if query == "faculty_sdg_bubble":
            query = """
                SELECT ModuleData.Faculty, SUM(StudentsPerModule.NumberOfStudents), COUNT(TestModAssign.Module_ID), COUNT(DISTINCT(TestModAssign.SDG)) FROM [dbo].[StudentsPerModule]
                INNER JOIN ModuleData ON StudentsPerModule.ModuleID = ModuleData.Module_ID
                INNER JOIN TestModAssign ON StudentsPerModule.ModuleID = TestModAssign.Module_ID
                GROUP BY ModuleData.Faculty;"""
            curr.execute(query)
            faculty_bubble_sdg = curr.fetchall()
            faculty_bubble_list = list()
            for faculties in faculty_bubble_sdg:
                faculty_bubble_list.append({
                    'Faculty': faculties[0],
                    'Number_Modules': faculties[2],
                    'SDG_Count': faculties[3],
                    'Number_Students': faculties[1]
                })

            colour_dict = {}
            for faculties in faculty_bubble_list:
                h, s, l = random.random(), 0.5 + random.random() / 2.0, 0.4 + random.random() / 5.0
                r, g, b = [int(256 * i) for i in colorsys.hls_to_rgb(h, l, s)]
                rgb = (round(r), round(g), round(b))
                colour_dict[str(faculties['Faculty'])] = '#%02x%02x%02x' % rgb

            checkboxes['value1'] = ''
            checkboxes['value2'] = ''
            checkboxes['value3'] = 'checked'
            return render(request, 'tableau_vis_ha.html',
                          {'selector': 'faculties', 'bubble_list': faculty_bubble_list, 'colours': colour_dict,
                           'radios': checkboxes, 'segment': tableauVisualisation})
    return render(request, 'tableau_vis_ha.html', {})
