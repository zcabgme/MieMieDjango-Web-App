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
from django.template.defaulttags import register
from .forms import BubbleChartAdd
from django.contrib.auth.decorators import login_required

import pyodbc
import json
import os
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
global_query, global_mod_sdg, global_pub_sdg = None, None, None
svm_context = {"data": None, "Predicted": None, "form": {"Default Preprocessor": "selected", "UCL Module Catalogue Preprocessor": ""}}
Module_CSV_Data, Publication_CSV_Data, IHE_CSV_Data = None, None, None
lda_threshold, svm_threshold, global_display_limit = 30, 30, 150

@login_required(login_url="/login/")
def index(request):
    context = {}
    context['segment'] = 'index'
    return render(request, 'index.html', context)

def app(request):
    global Module_CSV_Data
    global Publication_CSV_Data
    global global_context
    global global_query
    global global_mod_sdg, global_pub_sdg

    all_modules = Module.objects.all()[:10]
    all_publications = Publication.objects.all()[:10]

    form = {"modBox": "unchecked", "pubBox": "checked", "ASC": "selected", "DESC": ""}
    len_mod = Module.objects.count()
    len_pub = Publication.objects.count()
    context = {
        'mod': all_modules,
        'modules': None,
        'pub': all_publications,
        'publications': None,
        'len_mod': None,
        'len_pub': None,
        'form': form,
        'segment': 'app'
    }

    if request.method == 'GET':
        if "q" in request.GET:
            query = request.GET.get('q')
            print(query)

            if query == global_query and query != '' and query:
                context['pub'] = global_pub_sdg
                context['mod'] = global_mod_sdg

            elif query is not None and query != '' and len(query) != 0:
                global_pub_sdg = context['pub'] = Publication.objects.filter(data__icontains=query).distinct()
                lookups = Q(Department_Name__icontains=query) | Q(Department_ID__icontains=query) | Q(Module_Name__icontains=query) | Q(Module_ID__icontains=query) | Q(Faculty__icontains=query) | Q(Module_Lead__icontains=query) | Q(Description__icontains=query)
                global_mod_sdg = context['mod'] = Module.objects.filter(lookups).distinct()
                url_string = "q=" + str(query).replace(" ", "+")
                context['url_string'] = url_string + '&'
                global_query = query
            else:
                Module_CSV_Data = None
                Publication_CSV_Data = None

        # publications, modules = None, None
        # Module_CSV_Data, Publication_CSV_Data = None, None
        # len_mod, len_pub = 0, 0
        # if request.GET.get('modBox') == "clicked":
    
    mod_paginator = Paginator(context['mod'], 5)
    mod_page = request.GET.get('modPage')
    try:
        modules = mod_paginator.page(mod_page)
    except PageNotAnInteger:
        modules = mod_paginator.page(1)
    except EmptyPage:
        modules = mod_paginator.page(mod_paginator.num_pages)

    pub_paginator = Paginator(context['pub'], 5)
    pub_page = request.GET.get('pubPage')
    try:
        publications = pub_paginator.page(pub_page)
    except PageNotAnInteger:
        publications = pub_paginator.page(1)
    except EmptyPage:
        publications = pub_paginator.page(pub_paginator.num_pages)

    context['publications'] = publications
    context['modules'] = modules

    Module_CSV_Data = context['mod']
    context['len_mod'] = len(context['mod'])
    Publication_CSV_Data = context['pub']
    context['len_pub'] = len(context['pub'])

    
    context['pubs_classified'] = len([s for s in context['pub'] if s.assignedSDG['SVM_Prediction']!='' and s.assignedSDG['SVM_Prediction']])
    context['mods_classified'] = len([l for l in context['mod'] if l.assignedSDG['SVM_Prediction']!='' and l.assignedSDG['SVM_Prediction']])


    global_context = context
    return render(request, 'sdg_tables.html', context)


def bubble_chart_act(request):
    approach_list = ApproachAct.objects.all()
    specialty_list = SpecialtyAct.objects.all()
    colors = ColorAct.objects.all()
    bubbles = BubbleAct.objects.all()
    people = UserProfileAct.objects.all().count()

    approachNum = approach_list.count()
    specialtyNum = specialty_list.count()

    color_dict = {}
    approach_dict = {}
    bubble_dict = {}

    numSpecialty, numApproach = 0, 0

    for color in colors:
        specialty_dict = {}
        for specialty in specialty_list.filter(color=color):
            specialty_dict[specialty] = numSpecialty
            numSpecialty += 1
        color_dict[color] = specialty_dict

    for approach in approach_list:
        approach_dict[approach] = numApproach
        numApproach += 1

    CONST_1 = 45
    curr_max = 0
    for i in bubbles:
        if i.list_of_people.count(',') + 1 > curr_max:
            curr_max = i.list_of_people.count(',') + 1

    for bubble in bubbles:
        specialty_index = color_dict[bubble.color][bubble.coordinate_speciality] * CONST_1
        approach_index = approach_dict[bubble.coordinate_approach] * CONST_1
        areaNum = bubble.list_of_people.count(',') + 1
        size_raw = areaNum / curr_max

        z = ((size_raw) * (45 - 9)) + 9
        const = (z-9) / 36
        x = (-17 * const) + 13 + specialty_index
        y = (-16 * const) + 11 + approach_index

        bubble_dict[bubble] = [x, y, z]

    context = {'bubble_dict': bubble_dict, 'approach_dict': approach_dict,
               'color_dict': color_dict, 'verticalLength': approachNum + 1, 'horizontalLength': specialtyNum + 1}

    return render(request, 'bubble_chart_act.html', context)


def searchBubbleAct(request, pk=None, pk_alt=None):
    form = {"ALL": "selected", "UCL Authors": "unselected",
            "OTHER Authors": "unselected"}
    ucl_id = '60022148'
    obj = BubbleAct.objects.get(
        coordinate_approach=pk, coordinate_speciality=pk_alt)
    list_of_emails = obj.list_of_people.split(',')
    entry_list = []

    if request.method == 'POST':
        people = UserProfileAct.objects.all()
        query = request.POST.get('author_selection')

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

    num_of_people = len(entry_list)
    app_spec = [ApproachAct.objects.get(
        id=pk), SpecialtyAct.objects.get(id=pk_alt)]
    return render(request, 'searchBubbleAct.html', {"form": form, "entry_list": entry_list, "assignments": app_spec, "num_of_people": num_of_people})


def manual_add(request):
    approach_list = ApproachAct.objects.all()
    specialty_list = SpecialtyAct.objects.all()
    form = BubbleChartAdd()

    approach_select = {"Default": "unselected"}
    for i in approach_list:
        approach_select[i] = "unselected"

    speciality_select = {"Default": "unselected"}
    for i in specialty_list:
        speciality_select[i] = "unselected"

    if request.method == "POST":
        form = BubbleChartAdd(request.POST or None)

        if form.is_valid():
            form.save()
        else:
            saved_data = {
                "author_id": request.POST['author_id'],
                "fullName": request.POST['fullName'],
                "affiliation": request.POST['affiliation'],
                "approach": request.POST['approach'],
                "specialty": request.POST['specialty'],
                "form": form
            }
            messages.success(
                request, ("There was an error in your form! Please try again."))
            return render(request, 'manual_add.html', saved_data)

        messages.success(
            request, ("Your form has been submitted successfully!"))
        return redirect('manual_add')

    else:
        return render(request, 'manual_add.html', {"form": form, "approach_select": approach_select, "speciality_select": speciality_select})


# def getCheckBoxState(request, form):
#     # For SDG section, function reused (checkboxes and drop-down menu)
#     if 'Default' in form:
#         form['Default'] = "selected" if request.GET.get(
#             'sorting') == "Default" else "unselected"
#     if 'ASC' in form:
#         form['ASC'] = "selected" if request.GET.get(
#             'sorting') == "ASC" else "unselected"
#     if 'DESC' in form:
#         form['DESC'] = "selected" if request.GET.get(
#             'sorting') == "DESC" else "unselected"

#     # For main page checkboxes
#     form['modBox'] = "checked" if request.GET.get(
#         'modBox') == "clicked" else "unchecked"
#     form['pubBox'] = "checked" if request.GET.get(
#         'pubBox') == "clicked" else "unchecked"
#     form['iheBox'] = "checked" if request.GET.get(
#         'iheBox') == "clicked" else "unchecked"

#     return form


# def moduleSearch(request, query, all_publications, form):
#     lookups = Q(Department_Name__icontains=query) | Q(Department_ID__icontains=query) | Q(Module_Name__icontains=query) | Q(Module_ID__icontains=query) | Q(
#         Faculty__icontains=query) | Q(Module_Lead__icontains=query) | Q(Description__icontains=query)
#     myFilter = Module.objects.filter(lookups).distinct()
#     len_mod = myFilter.count()
#     len_pub = Publication.objects.count()
#     return {
#         'mod': myFilter,
#         'pub': all_publications,
#         'submitbutton': request.GET.get('submit'),
#         'len_mod': len_mod,
#         'len_pub': len_pub,
#         'len_total': len_mod + len_pub,
#         'form': form
#     }


# def publicationSearch(request, query, all_modules, form):
#     myFilter = Publication.objects.filter(data__icontains=query).distinct()
#     len_mod = Module.objects.count()
#     len_pub = myFilter.count()

#     return {
#         'mod': all_modules,
#         'pub': myFilter,
#         'submitbutton': request.GET.get('submit'),
#         'len_mod': len_mod,
#         'len_pub': len_pub,
#         'len_total': len_mod + len_pub,
#         'form': form
#     }


# def allSearch(request, query, all_modules, all_publications, form):
#     moduleResults = moduleSearch(request, query, all_modules, form)['mod']
#     publicationResults = publicationSearch(
#         request, query, all_modules, form)['pub']
#     len_mod = moduleResults.count()
#     len_pub = publicationResults.count()
#     return {
#         'mod': moduleResults,
#         'pub': publicationResults,
#         'submitbutton': request.GET.get('submit'),
#         'len_mod': len_mod,
#         'len_pub': len_pub,
#         'len_total': len_mod + len_pub,
#         'form': form
#     }


# def returnQuery(request, form, query, all_modules, all_publications):
#     global Module_CSV_Data
#     global Publication_CSV_Data
#     global global_context

#     if form['modBox'] == "checked" and form['pubBox'] == "unchecked":  # if only modules
#         context = moduleSearch(request, query, all_publications, form)
#         Module_CSV_Data = context["mod"]
#         Publication_CSV_Data = None
#     if form['modBox'] == "unchecked" and form['pubBox'] == "checked":  # if only publications
#         context = publicationSearch(request, query, all_modules, form)
#         Module_CSV_Data = None
#         Publication_CSV_Data = context["pub"]
#     elif form['modBox'] == "checked" and form['pubBox'] == "checked":  # if both
#         context = allSearch(request, query, all_modules, all_publications, form)
#         Module_CSV_Data = context["mod"]
#         Publication_CSV_Data = context["pub"]

#     global_context = context
#     return context


def iheVisualisation(request):
    client = pymongo.MongoClient(
        "mongodb+srv://admin:admin@cluster0.hw8fo.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
    db = client.Scopus
    col = db.Visualisations
    data = list(col.find())[0]

    context = {
        "pylda": data['PyLDA_ihe'],
        "tsne": data['TSNE_ihe']
    }
    client.close()
    return render(request, "visualisations/IHE/pyldavis.html", context)


def sdgVisualisation(request):
    client = pymongo.MongoClient(
        "mongodb+srv://admin:admin@cluster0.hw8fo.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
    db = client.Scopus
    col = db.Visualisations
    data = list(col.find())[1]

    context = {
        "pylda": data['PyLDA_sdg'],
        "tsne": data['TSNE_sdg']
    }
    client.close()
    return render(request, "visualisations/SDG/pyldavis.html", context)


def sortSDG_results(form, obj, ascending):
    return obj.order_by('assignedSDG__Validation__Similarity') if ascending else obj.order_by('-assignedSDG__Validation__Similarity')


def sdg(request):
    form = {"modBox": "unchecked", "pubBox": "unchecked",
            "Default": "unselected", "ASC": "unselected", "DESC": "unselected"}
    context = {
        'pub': Publication.objects.filter(assignedSDG__isnull=False).exclude(assignedSDG__SVM_Prediction=''),
        'mod': Module.objects.filter(Description__isnull=False),
        'lenPub': Publication.objects.count(),
        'lenMod': Module.objects.count(),
        'form': form,
    }

    if request.method == 'GET':
        query = request.GET.get('b')
        context['form'] = getCheckBoxState(request, form)

        if query is not None and query != '' and len(query) != 0:
            context = returnQuery(request, form, query,
                                  context['mod'], context['pub'])

        if context['form']['ASC'] == "selected":
            context['pub'] = sortSDG_results(
                form, context['pub'], ascending=True)
            context['mod'] = sortSDG_results(
                form, context['mod'], ascending=True)
        if context['form']['DESC'] == "selected":
            context['pub'] = sortSDG_results(
                form, context['pub'], ascending=False)
            context['mod'] = sortSDG_results(
                form, context['mod'], ascending=False)

        url_string = "b=" + str(query).replace(" ", "+") + \
            "&submit=" + str(request.GET.get('submit'))
        if request.GET.get('modBox') == "clicked":
            url_string = url_string + "&modBox=clicked"
        if request.GET.get('pubBox') == "clicked":
            url_string = url_string + "&pubBox=clicked"

        url_string = url_string + "&sorting=" + str(request.GET.get('sorting'))
        context['urlString'] = url_string

        pub_paginator = Paginator(context['pub'], 10)
        mod_paginator = Paginator(context['mod'], 10)

        pub_page = request.GET.get('pubPage')
        try:
            publications = pub_paginator.page(pub_page)
        except PageNotAnInteger:
            publications = pub_paginator.page(1)
        except EmptyPage:
            publications = pub_paginator.page(pub_paginator.num_pages)

        mod_page = request.GET.get('modPage')
        try:
            modules = mod_paginator.page(mod_page)
        except PageNotAnInteger:
            modules = mod_paginator.page(1)
        except EmptyPage:
            modules = mod_paginator.page(mod_paginator.num_pages)

        context['publications'] = publications
        context['modules'] = modules

        # Record the query results numbers
        context['lenMod'] = context['mod'].count()
        context['lenPub'] = context['pub'].count()

    return render(request, 'sdg.html', context)


def module(request, pk):
    try:
        module = Module.objects.get(id=pk)
    except Module.DoesNotExist:
        raise ("Module does not exist")
    return render(request, 'module.html', {'mod': module})


def publication(request, pk):
    try:
        publication = Publication.objects.get(id=pk)
    except Publication.DoesNotExist:
        raise ("Publication does not exist")
    return render(request, 'publication.html', {'pub': publication})


def export_modules_csv(request):
    global Module_CSV_Data
    global global_context
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
                                              "Module_ID", "Faculty", "Credit_Value", "Module_Lead", "Catalogue_Link", "Description")
        for module in modules:
            writer.writerow(module)
    except:
        messages.success(request, ("No modules to export! Please try again."))
        return render(request, 'index.html', global_context)

    return response


def export_publications_csv(request):
    global Publication_CSV_Data
    global global_context

    response = HttpResponse(content_type='text/csv')

    if not Publication_CSV_Data:
        messages.success(
            request, ("No publications to export! Please try again."))
        return render(request, 'index.html', global_context)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="publications.csv"'

    try:
        writer = csv.writer(response)
        writer.writerow(["Title", "EID", "DOI", "Year", "Source", "Volume", "Issue", "Page-Start", "Page-End", "Cited By",
                         "Link", "Abstract", "Author Keywords", "Index Keywords", "Dcoument Type", "Publication Stage", "Open Access", "Subject Areas", "UCL Authors Data", "Other Authors Data"])
    except:
        messages.success(
            request, ("No publications to export! Please try again."))
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
        if AuthorKeywords:
            AuthorKeywords = ','.join(AuthorKeywords)
        IndexKeywords = all_contents['IndexKeywords']
        if IndexKeywords:
            IndexKeywords = ','.join(IndexKeywords)
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
        UCLAuthorsData = []
        OtherAuthorsData = []
        if AuthorData:
            for id_ in AuthorData:
                name = AuthorData[id_]['Name']
                affiliationID = AuthorData[id_]['AffiliationID']
                affiliationName = AuthorData[id_]['AffiliationName']
                if affiliationID == "60022148":
                    if affiliationName:
                        UCLAuthorsData.append(
                            name + "(" + affiliationName + ")")
                    else:
                        UCLAuthorsData.append(name)
                else:
                    if name and not affiliationName:
                        OtherAuthorsData.append(','.join([name, ""]))
                    if not name and not affiliationName:
                        OtherAuthorsData.append("")
                    if name and affiliationName:
                        OtherAuthorsData.append(
                            name + "(" + affiliationName + ")")

        UCLAuthorsData = ','.join(UCLAuthorsData)
        OtherAuthorsData = ','.join(OtherAuthorsData)

        writer.writerow([title, EID, DOI, Year, Source, Volume, Issue, PageStart, PageEnd, CitedBy, Link, Abstract, AuthorKeywords,
                         IndexKeywords, DocumentType, PublicationStage, OpenAccess, SubjectAreas, UCLAuthorsData, OtherAuthorsData])

    return response


def unpickle_svm_model(filename):
    with open(filename, "rb") as input_file:
        return pickle.load(input_file)


def make_SVM_prediction(text, processor):
    svm = unpickle_svm_model("NLP/SVM/SDG/model.pkl")

    if processor == "module":
        preprocessor = ModuleCataloguePreprocessor()
    else:
        preprocessor = Preprocessor()
    predictions = svm.make_text_predictions(text, preprocessor)
    return predictions


def make_SVM_IHE_prediction(text):
    svm = unpickle_svm_model("NLP/SVM/IHE/model.pkl")
    preprocessor = Preprocessor()
    predictions = svm.make_text_predictions(text, preprocessor)
    return predictions


def check_svm_processor(request, form):
    form['Default Preprocessor'] = "checked" if request.GET.get(
        'sorting') == "Default Preprocessor" else ""
    form['UCL Module Catalogue Preprocessor'] = "checked" if request.GET.get(
        'sorting') == "UCL Module Catalogue Preprocessor" else ""
    return form


def drawDonutChart(results):
    fig, ax = plt.subplots(figsize=(10, 7), subplot_kw=dict(aspect="equal"))
    recipe = ["SDG 1", "SDG 2", "SDG 3", "SDG 4", "SDG 5", "SDG 6",
              "SDG 7", "SDG 8", "SDG 9", "SDG 10", "SDG 11", "SDG 12",
              "SDG 13", "SDG 14", "SDG 15", "SDG 16", "SDG 17", "Misc"]

    wedges, texts = ax.pie(results, wedgeprops=dict(width=0.5), startangle=-40)
    bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
    kw = dict(arrowprops=dict(arrowstyle="-"),
              bbox=bbox_props, zorder=0, va="center")

    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1)/2. + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        ax.annotate(recipe[i], xy=(x, y), xytext=(
            1.35*np.sign(x), 1.4*y), horizontalalignment=horizontalalignment, **kw)

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')
    return graphic


def drawDonutChartIHE(results):
    fig, ax = plt.subplots(figsize=(10, 7), subplot_kw=dict(aspect="equal"))
    recipe = ["IHE 1", "IHE 2", "IHE 3", "IHE 4", "IHE 5", "IHE 6",
              "IHE 7", "IHE 8", "IHE 9"]

    wedges, texts = ax.pie(results, wedgeprops=dict(width=0.5), startangle=-40)
    bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
    kw = dict(arrowprops=dict(arrowstyle="-"),
              bbox=bbox_props, zorder=0, va="center")

    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1)/2. + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        ax.annotate(recipe[i], xy=(x, y), xytext=(
            1.35*np.sign(x), 1.4*y), horizontalalignment=horizontalalignment, **kw)

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')
    return graphic


def truncate(n: float, decimals: int = 0) -> float:
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier


def universal_SVM(request):
    global svm_context

    if request.method == "GET":
        svm_context['form'] = check_svm_processor(request, svm_context['form'])
        query = request.GET.get('box')
        if svm_context['form']['UCL Module Catalogue Preprocessor'] == "checked":
            preprocessor = "module"
        else:
            preprocessor = "default"
        if query and query != "":
            prediction = make_SVM_prediction(query, processor=preprocessor)[0]
            prediction_list = prediction.tolist()
            results = []
            predicted_ = []
            for i in range(len(prediction_list)):
                temp = truncate(prediction_list[i] * 100, 1)
                results.append(temp)
                if temp >= svm_threshold:
                    predicted_.append(str(i + 1))
            svm_context["data"] = results
            svm_context["Predicted"] = ','.join(predicted_)
            svm_context["graphic"] = drawDonutChart(results)

            return render(request, 'svm.html', svm_context)
        else:
            return render(request, 'svm.html', {"data": None, "Predicted": None, "form": svm_context['form'], "graphic": None})

    return render(request, 'svm.html', svm_context)


def universal_SVM_IHE(request):
    svm_context = {}

    if request.method == "GET":
        query = request.GET.get('box')

        if query and query != "":
            prediction = make_SVM_IHE_prediction(query)[0]
            prediction_list = prediction.tolist()
            results = []
            predicted_ = []
            for i in range(len(prediction_list)):
                temp = truncate(prediction_list[i] * 100, 1)
                results.append(temp)
                if temp >= svm_threshold:
                    predicted_.append(str(i + 1))
            svm_context["data"] = results
            svm_context["Predicted"] = ','.join(predicted_)
            svm_context["graphic"] = drawDonutChartIHE(results)

            return render(request, 'ihe_universal_svm.html', svm_context)
        else:
            return render(request, 'ihe_universal_svm.html', {"data": None, "Predicted": None, "graphic": None})

    return render(request, 'ihe_universal_svm.html', svm_context)


def getCheckBoxState_ihe(request, form, number_of_ihe):
    for i in range(1, number_of_ihe+1):
        form[str(i)] = "selected" if request.GET.get(
            'prediction') == str(i) else "unselected"
    return form


def filter_ihe_by_prediction(context, key):
    return context.filter(assignedSDG__IHE_Prediction=key)


def export_ihe_csv(request):
    global IHE_CSV_Data

    if not IHE_CSV_Data:
        messages.success(
            request, ("No IHE publications to export! Please try again."))
        return render(request, 'ihe.html', {})

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="ihe_publications.csv"'

    try:
        writer = csv.writer(response)
        writer.writerow(["Name", "Prediction", "DOI", "Abstract"])
    except:
        messages.success(
            request, ("No IHE publications to export! Please try again."))
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


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


def ihe(request):
    global IHE_CSV_Data
    form = {"Default": "unselected"}
    number_of_ihe = 10

    lookup = {
        "1": "AI and Machine Learning",
        "2": "Bioinformatics",
        "3": "Cybersecurity",
        "4": "Data Sciences",
        "5": "Software Engineering",
        "6": "Robotics",
        "7": "Synthetic Biology",
        "8": "Pharmacology & Pharmaceuticals",
        "9": "Tissue Engineering & Regenerative Medicine",
    }

    for i in range(1, number_of_ihe+1):
        form[str(i)] = 'unselected'

    context = {
        'pub': Publication.objects.filter(assignedSDG__isnull=False),
        'lenPub': Publication.objects.count(),
        'form': form,
        'ihe_lookup': lookup
    }

    if request.method == 'GET':
        query = request.GET.get('c')
        context['form'] = getCheckBoxState_ihe(request, form, number_of_ihe)

        if query is not None and query != '' and len(query) != 0:
            context['pub'] = context['pub'].filter(
                data__icontains=query).distinct()

        for key, val in form.items():
            if val == "selected" and key != "Default":
                context['pub'] = filter_ihe_by_prediction(context['pub'], key)

        context['pub'] = context['pub'].filter(
            assignedSDG__IHE_SVM_Prediction__isnull=False)
        IHE_CSV_Data = context['pub']

        url_string = "c=" + str(query).replace(" ", "+") + \
            "&submit=" + str(request.GET.get('submit'))

        url_string = url_string + "&prediction=" + \
            str(request.GET.get('prediction'))
        context['urlString'] = url_string

        ihe_paginator = Paginator(context['pub'], 10)
        ihe_page = request.GET.get('ihePage')
        try:
            ihes = ihe_paginator.page(ihe_page)
        except PageNotAnInteger:
            ihes = ihe_paginator.page(1)
        except EmptyPage:
            ihes = ihe_paginator.page(ihe_paginator.num_pages)
        context['ihes'] = ihes

        return render(request, 'ihe.html', context)

    return render(request, 'ihe.html', {})


def getSQL_connection():
    server = 'summermiemieservver.database.windows.net'
    database = 'summermiemiedb'
    username = 'miemie_login'
    password = 'e_Paswrd?!'
    driver = '{ODBC Driver 17 for SQL Server}'
    myConnection = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server +
                                  ';PORT=1433;DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
    return myConnection


def tableauVisualisation(request):
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
                SELECT TestModAssign.SDG, COUNT(DISTINCT TestModAssign.Module_ID), SUM(StudentsPerModule.NumberOfStudents)
                FROM [dbo].[TestModAssign]
                INNER JOIN StudentsPerModule ON TestModAssign.Module_ID=StudentsPerModule.ModuleID 
                GROUP BY TestModAssign.SDG"""
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
            return render(request, 'tableau_vis.html', {'selector': 'modules', 'bubble_list': module_bubble_list, 'radios': checkboxes})

        if query == "department_sdg_bubble":
            query = """
                SELECT ModuleData.Department_Name, COUNT(TestModAssign.Module_ID), COUNT(DISTINCT(TestModAssign.SDG)), SUM(StudentsPerModule.NumberOfStudents) FROM [dbo].[ModuleData]
                INNER JOIN TestModAssign ON ModuleData.Module_ID = TestModAssign.Module_ID
                INNER JOIN StudentsPerModule ON ModuleData.Module_ID = StudentsPerModule.ModuleID
                GROUP BY ModuleData.Department_Name"""
            curr.execute(query)
            # (department name, num of modules, sdg coverage, num of students)
            department_bubble_sdg = curr.fetchall()
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
                h, s, l = random.random(), 0.5 + random.random()/2.0, 0.4 + random.random()/5.0
                r, g, b = [int(256*i) for i in colorsys.hls_to_rgb(h, l, s)]
                rgb = (round(r), round(g), round(b))
                colour_dict[str(departments['Department'])
                            ] = '#%02x%02x%02x' % rgb

            checkboxes['value1'] = ''
            checkboxes['value2'] = 'checked'
            checkboxes['value3'] = ''
            return render(request, 'tableau_vis.html', {'selector': 'departments', 'bubble_list': department_bubble_list, 'colours': colour_dict, 'radios': checkboxes})

        if query == "faculty_sdg_bubble":
            query = """
                SELECT ModuleData.Faculty, SUM(StudentsPerModule.NumberOfStudents), COUNT(TestModAssign.Module_ID), COUNT(DISTINCT(TestModAssign.SDG)) FROM [dbo].[StudentsPerModule]
                INNER JOIN ModuleData ON StudentsPerModule.ModuleID = ModuleData.Module_ID
                INNER JOIN TestModAssign ON StudentsPerModule.ModuleID = TestModAssign.Module_ID
                GROUP BY ModuleData.Faculty"""
            curr.execute(query)
            # (faculty name, num of students, num of modules, sdg coverage)
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
                h, s, l = random.random(), 0.5 + random.random()/2.0, 0.4 + random.random()/5.0
                r, g, b = [int(256*i) for i in colorsys.hls_to_rgb(h, l, s)]
                rgb = (round(r), round(g), round(b))
                colour_dict[str(faculties['Faculty'])] = '#%02x%02x%02x' % rgb

            checkboxes['value1'] = ''
            checkboxes['value2'] = ''
            checkboxes['value3'] = 'checked'
            return render(request, 'tableau_vis.html', {'selector': 'faculties', 'bubble_list': faculty_bubble_list, 'colours': colour_dict, 'radios': checkboxes})

    return render(request, 'tableau_vis.html', {})
