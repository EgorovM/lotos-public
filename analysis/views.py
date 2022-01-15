# -*- coding: utf-8 -*-

import os
import json
import codecs

import pandas

from django.utils.encoding import uri_to_iri
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.conf import settings

from analysis.models import AnalysInBranch, LabaratoryBranchShop, Matched, City
from analysis.models import Analys, GeneralLabaratory, LabaratoryBranch, SamplingType

from config.decorators import check_session_city_name


codecs.register(lambda name: codecs.lookup('utf8') if name == 'utf8mb4' else None)


@check_session_city_name('analysis:catalog')
def catalog(request, city_name):
    sections = sorted(Analys.get_sections_list())
    sections.append(sections[0]); sections.pop(0);
    city = City.get_city_by_name(city_name)

    section = request.GET.get('section', None)

    if not section is None:
        analysis = AnalysInBranch.objects.filter(labaratory_branch__city=city, analys__section=section.upper()).order_by('analys__code')[:25]
    else:
        analysis = AnalysInBranch.objects.filter(labaratory_branch__city=city).order_by('analys__code')[:25]

    return render(request, 'analysis/catalog.html', locals())


@check_session_city_name('analysis:analys')
def analys(request, city_name, name_en):
    city = City.get_city_by_name(city_name)
    analys = Analys.get_analys_by_name_en(name_en)

    branch_analys = AnalysInBranch.objects.filter(analys=analys, labaratory_branch__city=city).first()

    if branch_analys is None:
        return redirect('/eror')

    matcheds = Matched.find_matched_by_code(branch_analys.analys.code)

    if not matcheds is None:
        analys_list = matcheds.analysis_by_city(city)
        labaratory_list = [analys.labaratory_branch for analys in analys_list]
    else:
        analys_list = [branch_analys]
        labaratory_list = [branch_analys.labaratory_branch]

    title = branch_analys.name

    return render(request, 'analysis/analys.html', locals())


def map(request):
    points = LabaratoryBranchShop.objects.all()

    return render(request, 'search/analys_list.html', locals())


def search(request):
    return render(request, 'search/analys_list.html')


def dinamycal_search(request):
    if request.is_ajax():
        q = request.GET.get('term', '')
        city_name = request.session.get('city_name', 'sankt-peterburg')

        city = City.get_city_by_name(city_name)
        search_qs = AnalysInBranch.objects.filter(analys__name__icontains=q, labaratory_branch__city=city)[:25]

        results = []

        matched_ids = []

        for r in search_qs:
            if not r.is_buyable:
                continue

            matcheds = Matched.find_matched_by_code(r.analys.code)

            name = f"{r.labaratory_branch.name}: {r.analys.name}"

            if not matcheds is None:
                if matcheds.id in matched_ids:
                    continue

                matched_ids.append(matcheds.id)
                name = r.analys.name

            results.append({
                "id": r.analys.id,
                "branch_id": r.id,
                "name": name,
                "name_en": r.analys.name_en,
                "price": r.minimal_price,
            })

        data = eval(json.dumps(results))

        return JsonResponse(data, safe=False)

    return JsonResponse({'status': 'fail'})


def import_matcheds(request):
    Matched.objects.all().delete()

    df = pandas.read_csv(settings.BASE_DIR + f'/export_data/csv/matched.csv')

    for series_row in df.iloc:
        matched = Matched.from_dict(series_row.to_dict())
        matched.save()

    return HttpResponse(f"Добавлено {Matched.objects.all().count()} сопоставлений")


def import_samplings(request):
    df = pandas.read_csv(settings.BASE_DIR + f'/export_data/csv/samplings.csv')

    for series_row in df.iloc:
        sampling = SamplingType.from_dict(series_row.to_dict())
        sampling.save()

    return HttpResponse(f"Добавлено {SamplingType.objects.all().count()} сопоставлений")


def refresh_analys_sections(request):
    df = pandas.read_csv(settings.BASE_DIR + f'/export_data/csv/sections_connections.csv')
    df = df.fillna('ДРУГОЕ')

    d = {}

    for i, h, c in df.iloc:
        d[i] = i
        d[h] = i
        d[c] = i

    unexist = set()

    for analys in Analys.objects.all():
        if not analys.lab_section in d:
            unexist.add(analys.lab_section)
            continue

        analys.section = d[analys.lab_section]
        analys.save()

        if analys.id == 46797:
            print(analys, analys.section)

    return HttpResponse('Успешно изменено')


def import_shops(request):
    LabaratoryBranchShop.objects.all().delete()

    for city_name in os.listdir(settings.BASE_DIR + f'/export_data/Locations'):
        city = City.get_city_by_name(city_name)
        if city is None:
            continue

        for filename in os.listdir(settings.BASE_DIR + f'/export_data/Locations/' + city_name):
            if filename[-3:] != 'csv':
                continue

            df = pandas.read_csv(settings.BASE_DIR + f'/export_data/Locations/{city_name}/{filename}', sep='\t')

            for row in df.iloc:
                lab = LabaratoryBranch.objects.filter(city=city,
                        labaratory__name=row['lab_name']).first()

                if lab is None:
                    labaratory = GeneralLabaratory.objects.filter(
                        name=row['lab_name']
                    ).first()

                    if labaratory is None:
                        labaratory = GeneralLabaratory.objects.create(
                            name=row['lab_name']
                        )

                    lab = LabaratoryBranch.objects.create(
                        city=city,
                        labaratory=labaratory,
                    )

                LabaratoryBranchShop.objects.create(
                    labaratory=lab,
                    address=row['address'],
                    latitude=row['latitude'],
                    longitude=row['longitude'],
                    name=lab.name,
                    telephone=''
                )

    return HttpResponse('Успешно!')


def refresh_analysis(self):
    df = pandas.read_csv(settings.BASE_DIR + f'/export_data/analysis/analysis.csv', sep=';')
    errors = []

    for row in df.iloc:
        try:
            analys = AnalysInBranch.from_dict(row)

            if isinstance(analys, str):
                return HttpResponse(analys)
        except Exception as e:
            errors.append(e)

    return HttpResponse('Успешно' if len(errors) == 0 else str(errors))


def load_geojson(request):
    city_name = request.session.get('city_name', 'sankt-peterburg')
    city = City.get_city_by_name(city_name)

    result = city.shops_geojson()

    return JsonResponse(result)


def load_geojson_by_city_id(request, city_id):
    city = City.objects.get(id=city_id)
    result = city.shops_geojson()

    return JsonResponse(result)
