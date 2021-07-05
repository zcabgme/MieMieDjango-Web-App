from NLP.SVM.sdg_svm import SdgSvm
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

import pyodbc, json, os, csv, time
from io import BytesIO, StringIO
from colorsys import hsv_to_rgb
import matplotlib.pyplot as plt
from bson import json_util
import pymongo, pickle, base64
import numpy as np
import matplotlib
matplotlib.use('Agg')


global_context = {}
svm_context = {"data": None, "Predicted": None, "form": {"Default Preprocessor": "selected", "UCL Module Catalogue Preprocessor": ""}}
Module_CSV_Data, Publication_CSV_Data, IHE_CSV_Data = None, None, None
lda_threshold, svm_threshold, global_display_limit = 30, 30, 150


def app(request):
    global Module_CSV_Data
    global Publication_CSV_Data
    global global_context

    all_modules = Module.objects.all()
    all_publications = Publication.objects.all()


    form = {"modBox": "unchecked", "pubBox": "unchecked", "ASC": "selected", "DESC": ""}
    len_mod = Module.objects.count()
    len_pub = Publication.objects.count()
    context = {
        'mod': all_modules,
        'pub': all_publications,
        'len_mod': len_mod,
        'len_pub': len_pub,
        'len_total': len_mod + len_pub,
        'form': form
    }
    
    if request.method == 'GET':
        query = request.GET.get('q')
        form = getCheckBoxState(request, form)
        if query is not None and query != '' and len(query) != 0:
            context = returnQuery(request, form, query, all_modules, all_publications)
        else:
            Module_CSV_Data = None
            Publication_CSV_Data = None

        url_string = "q=" + str(query).replace(" ", "+") + "&submit=" + str(request.GET.get('submit'))
        if request.GET.get('modBox') == "clicked":
            url_string = url_string + "&modBox=clicked"
        if request.GET.get('pubBox') == "clicked":
            url_string = url_string + "&pubBox=clicked"
    
        pub_paginator = Paginator(context['pub'], 15)
        mod_paginator = Paginator(context['mod'], 15)

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

    len_mod = Module.objects.count()
    len_pub = Publication.objects.count()
    context = {
        'len_mod': len_mod,
        'len_pub': len_pub,
        'len_total': len_mod + len_pub,
        'form': form,
        'publications': publications,
        'modules': modules,
        'urlString': url_string
    }
    Module_CSV_Data = None
    Publication_CSV_Data = None
    global_context = context
    return render(request, 'index.html', context)

def bubble_chart(request):
    t0 = time.time()

    approach_list = Approach.objects.all()
    specialty_list = Specialty.objects.all()
    colors = Color.objects.all()
    bubbles = Bubble.objects.all()
    
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
    case = {
        # num_of_researchers: [left, top, bubble_size]
        1: [13, 11, 9],
        2: [12, 10, 12],
        3: [11, 8, 15],
        4: [9, 7, 18],
        5: [8, 5, 21],
        6: [6, 4, 24],
        7: [4, 3, 27],
        8: [3, 2, 30],
        9: [1, 2, 33],
        10:[1, -1, 36],
        11: [-2, -2, 39],
        12: [-3, -4, 42]
    }

    for bubble in bubbles:
        specialty_index = color_dict[bubble.color][bubble.coordinate_speciality] * CONST_1
        approach_index = approach_dict[bubble.coordinate_approach] * CONST_1
        areaNum = bubble.list_of_people.count(',') + 1

        if areaNum not in case: bubble_dict[bubble] = [specialty_index - 4, approach_index - 5, 45]
        else: bubble_dict[bubble] = [case[areaNum][0] + specialty_index, case[areaNum][1] + approach_index, case[areaNum][2]]
        
    context = {'bubble_dict': bubble_dict, 'approach_dict': approach_dict,
               'color_dict': color_dict, 'verticalLength': approachNum + 1, 'horizontalLength': specialtyNum + 1}

    return render(request, 'bubble_chart.html', context)    

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
    obj = BubbleAct.objects.get(coordinate_approach=pk,coordinate_speciality=pk_alt)
    list_of_emails = obj.list_of_people.split(',')
    entry_list = [UserProfileAct.objects.get(author_id=i) for i in list_of_emails]
    return render(request, 'searchBubble.html', {"entry_list": entry_list})

def searchBubble(request, pk=None, pk_alt=None):
    obj = Bubble.objects.get(coordinate_approach=pk, coordinate_speciality=pk_alt)
    list_of_emails = obj.list_of_people.split(',')
    entry_list = [UserProfile.objects.get(email=i) for i in list_of_emails]
    return render(request, 'searchBubble.html', {"entry_list": entry_list})

def clearEmptySDG_assignments():
    Publication.objects.filter(assignedSDG__isnull=True).delete()

def getCheckBoxState(request, form):
    # For SDG section, function reused (checkboxes and drop-down menu)
    if 'Default' in form:
        form['Default'] = "selected" if request.GET.get('sorting') == "Default" else "unselected"
    if 'ASC' in form:
        form['ASC'] = "selected" if request.GET.get('sorting') == "ASC" else "unselected"
    if 'DESC' in form:
        form['DESC'] = "selected" if request.GET.get('sorting') == "DESC" else "unselected"

    # For main page checkboxes
    form['modBox'] = "checked" if request.GET.get('modBox') == "clicked" else "unchecked"
    form['pubBox'] = "checked" if request.GET.get('pubBox') == "clicked" else "unchecked"
    form['iheBox'] = "checked" if request.GET.get('iheBox') == "clicked" else "unchecked"

    return form

def moduleSearch(request, query, all_publications, form):
    lookups = Q(Department_Name__icontains=query) | Q(Department_ID__icontains=query) | Q(Module_Name__icontains=query) | Q(Module_ID__icontains=query) | Q(
        Faculty__icontains=query) | Q(Module_Lead__icontains=query) | Q(Description__icontains=query)
    myFilter = Module.objects.filter(lookups).distinct()
    len_mod = myFilter.count()
    len_pub = Publication.objects.count()
    return {
        'mod': myFilter,
        'pub': all_publications,
        'submitbutton': request.GET.get('submit'),
        'len_mod': len_mod,
        'len_pub': len_pub,
        'len_total': len_mod + len_pub,
        'form': form
    }

def publicationSearch(request, query, all_modules, form):
    myFilter = Publication.objects.filter(data__icontains=query).distinct()
    len_mod = Module.objects.count()
    len_pub = myFilter.count()    

    return {
        'mod': all_modules,
        'pub': myFilter,
        'submitbutton': request.GET.get('submit'),
        'len_mod': len_mod,
        'len_pub': len_pub,
        'len_total': len_mod + len_pub,
        'form': form
    }

def allSearch(request, query, all_modules, all_publications, form):
    moduleResults = moduleSearch(request, query, all_modules, form)['mod']
    publicationResults = publicationSearch(request, query, all_modules, form)['pub']
    len_mod = moduleResults.count()
    len_pub = publicationResults.count()
    return {
        'mod': moduleResults,
        'pub': publicationResults,
        'submitbutton': request.GET.get('submit'),
        'len_mod': len_mod,
        'len_pub': len_pub,
        'len_total': len_mod + len_pub,
        'form': form
    }

def returnQuery(request, form, query, all_modules, all_publications):
    global Module_CSV_Data
    global Publication_CSV_Data
    global global_context

    if form['modBox'] == "checked" and form['pubBox'] == "unchecked":  # if only modules
        context = moduleSearch(request, query, all_publications, form)
        Module_CSV_Data = context["mod"]
        Publication_CSV_Data = None
    if form['modBox'] == "unchecked" and form['pubBox'] == "checked": # if only publications
        context = publicationSearch(request, query, all_modules, form)
        Module_CSV_Data = None
        Publication_CSV_Data = context["pub"]
    elif form['modBox'] == "checked" and form['pubBox'] == "checked":  # if both
        context = allSearch(request, query, all_modules, all_publications, form)
        Module_CSV_Data = context["mod"]
        Publication_CSV_Data = context["pub"]

    global_context = context
    return context

def iheVisualisation(request):
    client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.hw8fo.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
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
    client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.hw8fo.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
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
            context = returnQuery(request, form, query, context['mod'], context['pub'])
        
        if context['form']['ASC'] == "selected":
            context['pub'] = sortSDG_results(form, context['pub'], ascending=True)
            context['mod'] = sortSDG_results(form, context['mod'], ascending=True)
        if context['form']['DESC'] == "selected":
            context['pub'] = sortSDG_results(form, context['pub'], ascending=False)
            context['mod'] = sortSDG_results(form, context['mod'], ascending=False)

        url_string = "b=" + str(query).replace(" ", "+") + "&submit=" + str(request.GET.get('submit'))
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
        writer.writerow(["Department_Name", "Department_ID", "Module_Name", "Module_ID", "Faculty", "Credit_Value", "Module_Lead", "Catalogue_Link", "Description"])
        modules = Module_CSV_Data.values_list("Department_Name", "Department_ID", "Module_Name", "Module_ID", "Faculty", "Credit_Value", "Module_Lead", "Catalogue_Link", "Description")
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
        messages.success(request, ("No publications to export! Please try again."))
        return render(request, 'index.html', global_context)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="publications.csv"'

    try:
        writer = csv.writer(response)
        writer.writerow(["Title", "EID", "DOI", "Year", "Source", "Volume", "Issue", "Page-Start", "Page-End", "Cited By",
                         "Link", "Abstract", "Author Keywords", "Index Keywords", "Dcoument Type", "Publication Stage", "Open Access", "Subject Areas", "UCL Authors Data", "Other Authors Data"])
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

        writer.writerow([title, EID, DOI, Year, Source, Volume, Issue, PageStart, PageEnd, CitedBy, Link, Abstract, AuthorKeywords,
                         IndexKeywords, DocumentType, PublicationStage, OpenAccess, SubjectAreas, UCLAuthorsData, OtherAuthorsData])

    return response

def unpickle_svm_model():
    with open("NLP/SVM/model.pkl", "rb") as input_file:
        return pickle.load(input_file)

def make_SVM_prediction(text, processor):
    svm = unpickle_svm_model()

    if processor == "module":
        preprocessor = ModuleCataloguePreprocessor()
    else:
        preprocessor = Preprocessor()
    predictions = svm.make_text_predictions(text, preprocessor)
    return predictions

def check_svm_processor(request, form):
    form['Default Preprocessor'] = "checked" if request.GET.get('sorting') == "Default Preprocessor" else ""
    form['UCL Module Catalogue Preprocessor'] = "checked" if request.GET.get('sorting') == "UCL Module Catalogue Preprocessor" else ""
    return form

def drawDonutChart(results):
    fig, ax = plt.subplots(figsize=(10, 7), subplot_kw=dict(aspect="equal"))
    recipe = ["SDG 1", "SDG 2", "SDG 3", "SDG 4", "SDG 5", "SDG 6",
              "SDG 7", "SDG 8", "SDG 9", "SDG 10", "SDG 11", "SDG 12",
              "SDG 13", "SDG 14", "SDG 15", "SDG 16", "SDG 17", "Misc"]
   
    
    wedges, texts = ax.pie(results, wedgeprops=dict(width=0.5), startangle=-40)
    bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
    kw = dict(arrowprops=dict(arrowstyle="-"),bbox=bbox_props, zorder=0, va="center")

    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1)/2. + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        ax.annotate(recipe[i], xy=(x, y), xytext=(1.35*np.sign(x), 1.4*y), horizontalalignment=horizontalalignment, **kw)

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')
    return graphic

def truncate(n:float, decimals:int =0) -> float:
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

def getCheckBoxState_ihe(request, form, number_of_ihe):
    for i in range(1, number_of_ihe+1):
        form[str(i)] = "selected" if request.GET.get('prediction') == str(i) else "unselected"
    return form

def filter_ihe_by_prediction(context, key):
    return context.filter(assignedSDG__IHE_Prediction=key)

def export_ihe_csv(request):
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
        "9": "Tissue Engineering",
        "10": "Regenerative Medicine"
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
            context['pub'] = context['pub'].filter(data__icontains=query).distinct()

        for key, val in form.items():
            if val == "selected" and key != "Default":
                context['pub'] = filter_ihe_by_prediction(context['pub'], key)

        IHE_CSV_Data = context['pub']

        url_string = "c=" + str(query).replace(" ", "+") + "&submit=" + str(request.GET.get('submit'))
        
        url_string = url_string + "&prediction=" + str(request.GET.get('prediction'))
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
    myConnection = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server +';PORT=1433;DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
    return myConnection

def tableauVisualisation(request):
    curr = getSQL_connection().cursor()
    checkboxes = {'value1': '', 'value2': '', 'value3': ''}

    if request.method == 'GET':
        query = request.GET.get('exampleRadios')

        if query == "sdg_bubble":
            query = """
                SELECT TestModAssign.SDG, COUNT(DISTINCT TestModAssign.Module_ID), SUM(StudentsPerModule.NumberOfStudents)
                FROM [dbo].[TestModAssign]
                INNER JOIN StudentsPerModule ON TestModAssign.Module_ID=StudentsPerModule.ModuleID 
                GROUP BY TestModAssign.SDG"""
            curr.execute(query)
            sdg_bubbles = curr.fetchall() # (assigned sdg, module id, number of students)
            module_bubble_list = list()
            for sdg in sdg_bubbles:
                module_bubble_list.append({
                    'SDG': str(sdg[0]),
                    'Number_Students': sdg[2],
                    'Number_Modules': sdg[1]
                })
            # module_bubble_sdg = json.dumps(sdg_bubble_list)
            with open('static/js/bubble.json', 'w') as f:
                json.dump(module_bubble_list, f)

            checkboxes['value1'] = 'checked'
            checkboxes['value2'] = ''
            checkboxes['value3'] = ''
            return render(request, 'tableau_vis.html', {'selector': 'modules', 'radios': checkboxes})

        if query == "department_sdg_bubble":
            query = """
                SELECT ModuleData.Department_Name, COUNT(TestModAssign.Module_ID), COUNT(DISTINCT(TestModAssign.SDG)), SUM(StudentsPerModule.NumberOfStudents) FROM [dbo].[ModuleData]
                INNER JOIN TestModAssign ON ModuleData.Module_ID = TestModAssign.Module_ID
                INNER JOIN StudentsPerModule ON ModuleData.Module_ID = StudentsPerModule.ModuleID
                GROUP BY ModuleData.Department_Name"""
            curr.execute(query)
            department_bubble_sdg = curr.fetchall() # (department name, num of modules, sdg coverage, num of students)
            department_bubble_list = list()
            for departments in department_bubble_sdg:
                print(departments[0])
                department_bubble_list.append({
                    'Department': departments[0],
                    'Number_Modules': departments[1],
                    'SDG_Count': departments[2],
                    'Number_Students': departments[3]
                })
            with open('static/js/bubble.json', 'w') as f:
                json.dump(department_bubble_list, f)

            checkboxes['value1'] = ''
            checkboxes['value2'] = 'checked'
            checkboxes['value3'] = ''
            return render(request, 'tableau_vis.html', {'selector': 'departments', 'radios': checkboxes})

        if query == "faculty_sdg_bubble":
            query = """
                SELECT ModuleData.Faculty, SUM(StudentsPerModule.NumberOfStudents), COUNT(TestModAssign.Module_ID), COUNT(DISTINCT(TestModAssign.SDG)) FROM [dbo].[StudentsPerModule]
                INNER JOIN ModuleData ON StudentsPerModule.ModuleID = ModuleData.Module_ID
                INNER JOIN TestModAssign ON StudentsPerModule.ModuleID = TestModAssign.Module_ID
                GROUP BY ModuleData.Faculty"""
            curr.execute(query)
            faculty_bubble_sdg = curr.fetchall() # (faculty name, num of students, num of modules, sdg coverage)
            checkboxes['value1'] = ''
            checkboxes['value2'] = ''
            checkboxes['value3'] = 'checked'
            return render(request, 'tableau_vis.html', {'selector': faculty_bubble_sdg, 'radios': checkboxes})

    return render(request, 'tableau_vis.html', {})

    if selector == 3:
        query = """
            SELECT TestModAssign.SDG, COUNT(DISTINCT TestModAssign.Module_ID), SUM(StudentsPerModule.NumberOfStudents)
            FROM [dbo].[TestModAssign]
            INNER JOIN StudentsPerModule ON TestModAssign.Module_ID=StudentsPerModule.ModuleID 
            GROUP BY TestModAssign.SDG"""
        curr.execute(query)
        sdg_bubbles = curr.fetchall() # (assigned sdg, module id, number of students)
        module_bubble_list = list()
        for sdg in sdg_bubbles:
            module_bubble_list.append({
                'SDG': str(sdg[0]),
                'Number_Students': sdg[2],
                'Number_Modules': sdg[1]
            })
        # module_bubble_sdg = json.dumps(sdg_bubble_list)
        with open('static/js/bubble.json', 'w') as f:
            json.dump(module_bubble_list, f)
        context = {'selector': "modules"}

    # context = {
    #     'Faculty_SDG_Bubble': faculty_bubble_sdg,
    #     'Department_SDG_Bubble': department_bubble_sdg,
    #     'Module_SDG_Bubble': module_bubble_sdg
    #     'vis_type': 
    # }

    return render(request, 'tableau_vis.html', context)
