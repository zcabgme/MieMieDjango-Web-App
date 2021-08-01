from django.urls import path, include
from django.conf.urls.static import static  # new
from django.conf import settings  # new
from django.conf.urls import url
from app import views
from django.contrib.staticfiles.views import serve
from django.views.decorators.cache import cache_control

urlpatterns = [
    path('', views.app, name='app'),
    # path('bubble_chart', views.bubble_chart, name='bubble_chart'),
    path('bubble_chart_act', views.bubble_chart_act, name='bubble_chart_act'),
    # url(r'searchBubble/(?P<pk>\d+)/(?P<pk_alt>\d+)/$', views.searchBubble, name='searchBubble'),
    url(r'searchBubbleAct/(?P<pk>\d+)/(?P<pk_alt>\d+)/$',views.searchBubbleAct, name='searchBubbleAct'),
    path('sdg', views.sdg, name='sdg'),
    path('ihe', views.ihe, name='ihe'),
    path('svm_universal', views.universal_SVM, name='universal_SVM'),
    path('iheVisualisation', views.iheVisualisation, name='iheVisualisation'),
    path('sdgVisualisation', views.sdgVisualisation, name='sdgVisualisation'),
    path('tableauVisualisation', views.tableauVisualisation, name='tableauVisualisation'),
    path('module/<str:pk>', views.module, name='module'),
    path('publication/<str:pk>', views.publication, name='publication'),
    path('exportMod', views.export_modules_csv, name='export_modules_csv'),
    path('exportPub', views.export_publications_csv,name='export_publications_csv'),
    path('export_ihe_csv', views.export_ihe_csv, name='export_ihe_csv'),
    path('manual_add', views.manual_add, name='manual_add'),
<<<<<<< Updated upstream
=======
    path('auth', views.auth, name='auth'),
    path('idp/profile/SAML2/Redirect/SSO', views.redirect, name='redirect'),
    
    
    # Matches any html file
    # re_path(r'^.*\.*', views.pages, name='pages'),
>>>>>>> Stashed changes
]

# if settings.DEBUG:
#     urlpatterns += static(settings.STATIC_URL,
#                           view=cache_control(no_cache=True, must_revalidate=True)(serve))
