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
from django.views.decorators.csrf import csrf_exempt
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
global_query, global_mod_sdg_paginator, global_pub_sdg_paginator, global_ihe_paginator = None, None, None, None
svm_context = {"data": None, "Predicted": None,
               "form": {"Default Preprocessor": "selected", "UCL Module Catalogue Preprocessor": ""}}
Module_CSV_Data, Publication_CSV_Data, IHE_CSV_Data = None, None, None
lda_threshold, svm_threshold, paginator_limiter = 30, 30, 10


# @login_required(login_url="/login/")
def index(request):
    return render(request, 'index.html', {"segment": "index"})


# @login_required(login_url="/login/")
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

                global_pub_sdg_paginator, global_mod_sdg_paginator = Paginator(context['pub'],
                                                                               paginator_limiter), Paginator(
                    context['mod'], paginator_limiter)

            else:
                Module_CSV_Data, Publication_CSV_Data = None, None

            url_string = "q=" + str(query).replace(" ", "+")

        else:
            global_mod_sdg_paginator, global_pub_sdg_paginator = Paginator(context['mod'],
                                                                           paginator_limiter), Paginator(context['pub'],
                                                                                                         paginator_limiter)
            global_query = None

        mod_page = request.GET.get('modPage')
        try:
            modules = global_mod_sdg_paginator.page(mod_page)
        except PageNotAnInteger:
            modules = global_mod_sdg_paginator.page(1)
        except EmptyPage:
            modules = global_mod_sdg_paginator.page(global_mod_sdg_paginator.num_pages)
        context['modules'] = modules

        pub_page = request.GET.get('pubPage')
        try:
            publications = global_pub_sdg_paginator.page(pub_page)
        except PageNotAnInteger:
            publications = global_pub_sdg_paginator.page(1)
        except EmptyPage:
            publications = global_pub_sdg_paginator.page(global_pub_sdg_paginator.num_pages)
        context['publications'] = publications

        Module_CSV_Data, Publication_CSV_Data = context['mod'], context['pub']

        if url_string != "": url_string = url_string + "&"
        context['url_string'] = url_string

    context['len_mod'] = global_mod_sdg_paginator.count
    context['len_pub'] = global_pub_sdg_paginator.count

    global_context = context
    return render(request, 'search_engine.html', context)


# @login_required(login_url="/login/")
def bubble_chart_act(request):
    approach_list = ApproachAct.objects.all().values_list('id', flat=True)
    speciality_list = SpecialtyAct.objects.all().values_list('id', flat=True)
    bubbles = BubbleAct.objects.all()
    approach_dict = {int(i.id): i.name for i in ApproachAct.objects.all()}
    speciality_dict = {int(i.id): i for i in SpecialtyAct.objects.all()}

    CONST_SCALE_MAX, SIZE_MIN = 25, 9
    curr_max = 0
    for i in bubbles:
        if i.list_of_people.count(',') + 1 > curr_max:
            curr_max = i.list_of_people.count(',') + 1

    bubble_dict = {}
    for i in approach_list:
        bubble_dict[approach_dict[i]] = {}
        for j in speciality_list:
            try:
                bubble_obj = bubbles.get(coordinate_approach=int(i), coordinate_speciality=int(j))
                size = (((bubble_obj.list_of_people.count(',') + 1) / curr_max) * (
                            CONST_SCALE_MAX - SIZE_MIN)) + SIZE_MIN
                bubble_dict[approach_dict[i]][int(j)] = [bubble_obj, size]
            except:
                bubble_dict[approach_dict[i]][int(j)] = None

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
    form = {"ALL": "selected", "UCL Authors": "unselected", "OTHER Authors": "unselected"}
    ucl_id = '60022148'
    obj = BubbleAct.objects.get(coordinate_approach=pk, coordinate_speciality=pk_alt)
    list_of_emails = obj.list_of_people.split(',')
    entry_list = []

    if request.method == 'GET':
        people = UserProfileAct.objects.all()
        query = request.GET.get('author_selection')

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

        author_paginator = Paginator(entry_list, 10)
        author_page = request.GET.get('page')
        try:
            authors = author_paginator.page(author_page)
        except PageNotAnInteger:
            authors = author_paginator.page(1)
        except EmptyPage:
            authors = author_paginator.page(global_ihe_paginator.num_pages)

    url_string = 'csrfmiddlewaretoken=' + str(request.GET.get('csrfmiddlewaretoken')) + '&author_selection=' + str(
        request.GET.get('author_selection')).replace(" ", "+") + "&"

    num_of_people = len(entry_list)
    app_spec = [ApproachAct.objects.get(id=pk), SpecialtyAct.objects.get(id=pk_alt), pk, pk_alt]

    return render(request, 'search_bubble.html',
                  {"form": form, "entry_list": authors, "assignments": app_spec, "num_of_people": num_of_people,
                   "url_string": url_string})

    return render(request, 'search_bubble.html',
                  {"form": form, "entry_list": authors, "assignments": app_spec, "num_of_people": num_of_people,
                   "url_string": url_string})


# @login_required(login_url="/login/")
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
        return render(request, 'manual_add.html',
                      {"form": form, "approach_select": approach_select, "speciality_select": speciality_select})


# @login_required(login_url="/login/")
def iheVisualisation(request):
    client = pymongo.MongoClient(get_details('MONGO_DB', 'client'))
    col = client.Scopus.Visualisations
    data = list(col.find())[0]

    context = {
        "pylda": data['PyLDA_ihe'],
        "tsne": data['TSNE_ihe'],
        "segment": "iheVisualisation"
    }
    client.close()
    return render(request, "ihe_model_vis.html", context)


# @login_required(login_url="/login/")
def sdgVisualisation(request):
    client = pymongo.MongoClient(get_details('MONGO_DB', 'client'))
    col = client.Scopus.Visualisations
    data = list(col.find())[1]

    context = {
        "pylda": data['PyLDA_sdg'],
        "tsne": data['TSNE_sdg'],
        "segment": "sdgVisualisation"
    }
    client.close()
    return render(request, "sdg_model_vis.html", context)


def sdg(request):
    global global_context
    global global_query
    global global_mod_sdg_paginator, global_pub_sdg_paginator

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
            query = request.GET.get('q')

            if query is not None and query != '' and len(query) != 0 and query != global_query:
                context['pub'] = Publication.objects.filter(data__icontains=query).distinct()
                lookups = Q(Department_Name__icontains=query) | Q(Department_ID__icontains=query) | Q(
                    Module_Name__icontains=query) | Q(Module_ID__icontains=query) | Q(Faculty__icontains=query) | Q(
                    Module_Lead__icontains=query) | Q(Description__icontains=query)
                context['mod'] = Module.objects.filter(lookups).distinct()
                global_query = query
                global_pub_sdg_paginator, global_mod_sdg_paginator = Paginator(context['pub'], 10), Paginator(
                    context['mod'], 10)
            url_string = "q=" + str(query).replace(" ", "+")

        else:
            global_pub_sdg_paginator, global_mod_sdg_paginator = Paginator(context['pub'], 10), Paginator(
                context['mod'], 10)
            global_query = None

        mod_page = request.GET.get('modPage')
        try:
            modules = global_mod_sdg_paginator.page(mod_page)
        except PageNotAnInteger:
            modules = global_mod_sdg_paginator.page(1)
        except EmptyPage:
            modules = global_mod_sdg_paginator.page(global_mod_sdg_paginator.num_pages)
        context['modules'] = modules

        pub_page = request.GET.get('pubPage')
        try:
            publications = global_pub_sdg_paginator.page(pub_page)
        except PageNotAnInteger:
            publications = global_pub_sdg_paginator.page(1)
        except EmptyPage:
            publications = global_pub_sdg_paginator.page(global_pub_sdg_paginator.num_pages)
        context['publications'] = publications

        context['len_mod'] = global_mod_sdg_paginator.count
        context['len_pub'] = global_pub_sdg_paginator.count

    # global_context = context
    return render(request, 'sdg_tables.html', context)


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


def ihe(request):
    """
       IHE assignments display page
       Allows for search and filtering by IHE assignment 
    """

    global global_query, global_ihe_paginator, IHE_CSV_Data

    form = {"Default": "unselected"}
    number_of_ihe = 9

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

    for i in range(1, number_of_ihe + 1):
        form[str(i)] = 'unselected'

    context = {
        'pub': Publication.objects.all(),
        'len_pub': Publication.objects.count(),
        'form': form,
        'ihe_lookup': lookup,
        'segment': 'ihe'
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
            if val == "selected" and key != "Default":
                context['pub'] = context['pub'].filter(assignedSDG__IHE_Prediction=key)
                global_ihe_paginator = Paginator(context['pub'], paginator_limiter)
                url_string = url_string + "&prediction=" + str(request.GET.get('prediction'))

        ihe_page = request.GET.get('ihePage')
        try:
            ihes = global_ihe_paginator.page(ihe_page)
        except PageNotAnInteger:
            ihes = global_ihe_paginator.page(1)
        except EmptyPage:
            ihes = global_ihe_paginator.page(global_ihe_paginator.num_pages)
        context['ihes'] = ihes

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

    server = get_details('SQL_SERVER', 'server')
    database = get_details('SQL_SERVER', 'database')
    username = get_details('SQL_SERVER', 'username')
    password = get_details('SQL_SERVER', 'password')
    driver = get_details('SQL_SERVER', 'driver')
    myConnection = pyodbc.connect(
        'DRIVER=' + driver + ';SERVER=' + server + ';PORT=1433;DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
    return myConnection


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
            return render(request, 'tableau_vis.html',
                          {'selector': 'modules', 'bubble_list': module_bubble_list, 'radios': checkboxes,
                           'segment': tableauVisualisation})

        if query == "department_sdg_bubble":
            query = """
                SELECT ModuleData.Department_Name, COUNT(TestModAssign.Module_ID), COUNT(DISTINCT(TestModAssign.SDG)), SUM(StudentsPerModule.NumberOfStudents) FROM [dbo].[ModuleData]
                INNER JOIN TestModAssign ON ModuleData.Module_ID = TestModAssign.Module_ID
                INNER JOIN StudentsPerModule ON ModuleData.Module_ID = StudentsPerModule.ModuleID
                GROUP BY ModuleData.Department_Name"""
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
                SELECT ModuleData.Faculty, SUM(StudentsPerModule.NumberOfStudents), COUNT(TestModAssign.Module_ID), COUNT(DISTINCT(TestModAssign.SDG)) FROM [dbo].[StudentsPerModule]
                INNER JOIN ModuleData ON StudentsPerModule.ModuleID = ModuleData.Module_ID
                INNER JOIN TestModAssign ON StudentsPerModule.ModuleID = TestModAssign.Module_ID
                GROUP BY ModuleData.Faculty"""
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
