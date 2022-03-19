from django.urls import path, include
from django.conf.urls.static import static  # new
from django.conf import settings  # new
from django.conf.urls import url
from app import views
from django.contrib.staticfiles.views import serve
from django.views.decorators.cache import cache_control

urlpatterns = [
    path('', views.index, name='index'),

    path('app', views.app, name='app'),
    path('bubble_chart_act', views.bubble_chart_act, name='bubble_chart_act'),
    url(r'searchBubbleAct/(?P<pk>\d+)/(?P<pk_alt>\d+)/$',views.searchBubbleAct, name='searchBubbleAct'),
    path('sdg', views.sdg, name='sdg'),
    path('ihe', views.ihe, name='ihe'),
    path('svm_universal', views.universal_SVM, name='universal_SVM'),
    path('universal_SVM_IHE', views.universal_SVM_IHE, name='universal_SVM_IHE'),
    
    path('iheVisualisation', views.iheVisualisation, name='iheVisualisation'),
    path('sdgVisualisation', views.sdgVisualisation, name='sdgVisualisation'),
    path('tableauVisualisation', views.tableauVisualisation, name='tableauVisualisation'),
    path('tableauVisualisationHA', views.tableauVisualisationHA, name='tableauVisualisationHA'),
    path('selectSDGorFaculty', views.selectSDGorFaculty, name='selectSDGorFaculty'),
    path('module/<str:pk>', views.module, name='module'),
    path('publication/<str:pk>', views.publication, name='publication'),
    path('exportMod', views.export_modules_csv, name='export_modules_csv'),
    path('exportPub', views.export_publications_csv,name='export_publications_csv'),
    path('export_ihe_csv', views.export_ihe_csv, name='export_ihe_csv'),
    path('manual_add', views.manual_add, name='manual_add'),
    path('SDG1', views.SDG1, name='SDG1'),
    path('Faculty1', views.Faculty1, name='Faculty1'),
    path('SDG2', views.SDG2, name='SDG2'),
    path('Faculty2', views.Faculty2, name='Faculty2'),
    path('SDG3', views.SDG3, name='SDG3'),
    path('Faculty3', views.Faculty3, name='Faculty3'),
    path('SDG4', views.SDG4, name='SDG4'),
    path('SDG5', views.SDG5, name='SDG5'),
    path('SDG6', views.SDG6, name='SDG6'),
    path('SDG7', views.SDG7, name='SDG7'),
    path('SDG8', views.SDG8, name='SDG8'),
    path('SDG9', views.SDG9, name='SDG9'),
    path('SDG10', views.SDG10, name='SDG10'),
    path('SDG11', views.SDG11, name='SDG11'),
    path('SDG12', views.SDG12, name='SDG12'),
    path('SDG13', views.SDG13, name='SDG13'),
    path('SDG14', views.SDG14, name='SDG14'),
    path('SDG15', views.SDG15, name='SDG15'),
    path('SDG16', views.SDG16, name='SDG16'),
    path('SDG17', views.SDG17, name='SDG17'),
    path('Faculty4', views.Faculty4, name='Faculty4'),
    path('Faculty5', views.Faculty5, name='Faculty5'),
    path('Faculty6', views.Faculty6, name='Faculty6'),
    path('Faculty7', views.Faculty7, name='Faculty7'),
    path('Faculty8', views.Faculty8, name='Faculty8'),
    path('Faculty9', views.Faculty9, name='Faculty9'),
    path('Faculty10', views.Faculty10, name='Faculty10'),
    path('Faculty11', views.Faculty11, name='Faculty11'),
    path('Faculty12', views.Faculty12, name='Faculty12'),
    path('viewInformationSDG', views.viewInformationSDG, name='viewInformationSDG'),
    path('viewInformationFaculty', views.viewInformationFaculty, name='viewInformationFaculty'),
    # path('auth', views.auth, name='auth'),
    # path('idp/profile/SAML2/Redirect/SSO', views.redirect, name='redirect'),
    
    
    # Matches any html file
    # re_path(r'^.*\.*', views.pages, name='pages'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          view=cache_control(no_cache=True, must_revalidate=True)(serve))
