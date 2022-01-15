from django.conf.urls.static import static
from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.shortcuts import render

from other import views

app_name = "other"

def htaccess(request, filename):
    return render(request, f'old/{filename}')


urlpatterns = [
    path('', views.index, name='index'),
    path('coronavirus-spb/', views.coronavirus_spb, name='coronavirus-spb'),
    path('coronavirus-moskva/', views.coronavirus_moskva, name='coronavirus-moskva'),
    path('moskva/coronavirus/', views.coronavirus_moskva),
    path('sankt-peterburg/coronavirus/', views.coronavirus_spb),

    path('o-nas/', views.about, name='about'),

    path('doctors/', views.partners, name='partners'),
    path('doctors/<str:specialization_en>/<str:name_en>', views.partner, name='partner'),
    path('import_partners/', views.import_partners),

    path('add_question/', views.add_question, name='add_question'),
    path('add_interview/', views.add_interview, name='add_interview'),

    path('generate_cart_url/', views.generate_cart_url, name='generate_cart_url'),
]


old_urls = [
    ('privacy', 'page11778076.html'),
    ('eror', 'page11813515.html'),
    ('user-agreement', 'page12139654.html'),
    ('dogovor', 'page12141102.html'),
    ('coronavirus-deviatkino', 'page12572737.html'), ('coronavirus-murino', 'page12572797.html'), ('coronavirus-kolpino', 'page12577456.html'), ('coronavirus-kudrovo', 'page12581296.html'), ('coronavirus-gatchina', 'page12581410.html'), ('coronavirus-kirovsk', 'page12581620.html'), ('coronavirus-viborg', 'page12581725.html'), ('coronavirus-nevskii-rayon', 'page12581783.html'), ('coronavirus-krasnoselski-rayon', 'page12581866.html'), ('coronavirus-primoskii-rayon', 'page12581951.html'), ('coronavirus-viborgskii-rayon', 'page12582070.html'), ('coronavirus-kalininskii-rayon', 'page12582193.html'), ('coronavirus-moskovskii-rayon', 'page12582287.html')]

urlpatterns += [
    path(name, htaccess, name=name, kwargs={'filename': filename})
    for name, filename in old_urls
]
