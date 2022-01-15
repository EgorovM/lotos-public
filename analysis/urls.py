from django.conf.urls.static import static
from django.contrib import admin
from django.conf import settings
from django.urls import path, include

from analysis import views

app_name = "analysis"

urlpatterns = [
    path('analizy-<str:city_name>/katalog-analizov/', views.catalog, name='catalog'),
    path('analizy-<str:city_name>/katalog-analizov/<str:name_en>/', views.analys, name='analys'),

    path('load_geojson_by_city_id/<int:city_id>/', views.load_geojson_by_city_id, name='load_geojson_by_city_name'),
    path('load_geojson/', views.load_geojson, name='load_geojson'),
    path('get_labaratories/', views.map, name='map'),
    path('search/', views.search, name='search'),
    path('ajax_calls/search/', views.dinamycal_search),

    path('import_matcheds/', views.import_matcheds),
    path('import_samplings/', views.import_samplings),
    path('refresh_analysis', views.refresh_analysis),
    path('refresh_analys_sections/', views.refresh_analys_sections),
    path('import_shops/', views.import_shops),
]
