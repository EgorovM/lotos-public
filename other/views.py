import os

import pandas
from transliterate import translit

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.conf import settings

from analysis.models import City, Analys
from other.models import Question, Interview, Partner, PartnerPackage

from config.decorators import check_session_city_name


def index(request):
    return render(request, 'main/home.html', locals())


def coronavirus_spb(request):
    city = City.get_city_by_name('sankt-peterburgkoronavirus')
    city_name = 'Санкт-Петербург'
    city_name_sk = 'Санкт-Петербурге'
    helix_code = 46068
    invitro_code = 46069

    return render(request, 'main/Coronavirus_page.html', locals())


def coronavirus_moskva(request):
    city = City.get_city_by_name('moskvakoronavirus')
    city_name = 'Москва'
    city_name_sk = 'Москве'
    helix_code = 79226
    invitro_code = 79227

    return render(request, 'main/Coronavirus_page.html', locals())


def about(request):
    return render(request, 'main/about_us.html', locals())


def partners(request):
    specializations = Partner.get_specialization()
    specialization = request.GET.get('specialization', None)

    if not specialization is None:
        partners = Partner.objects.filter(specialization=specialization)
    else:
        partners = Partner.objects.all()

    return render(request, 'main/partners.html', locals())


def partner(request, specialization_en, name_en):
    partner = Partner.get_partner_by_spec_name(specialization_en, name_en)

    if partner is None:
        return redirect('/eror')

    return render(request, 'main/partner.html', locals())


def add_question(request):
    error = 1

    if request.method == "POST":
        question = Question.add_question_by_post(request.POST)
        question.save()

        error = 0

        send_mail(
            'lotoslab.ru вопрос',
            f'{question.get_html()}',
            settings.EMAIL_HOST_USER,
            ['egorov_michil@mail.ru'] + settings.SEND_TO_EMAILS,
            fail_silently=True,
        )

    return redirect(request.META.get('HTTP_REFERER', '/'))


def add_interview(request):
    error = 1

    if request.method == "POST":
        interview = Interview.add_by_post(request.POST)
        interview.save()
        error = 0

        send_mail(
            'lotoslab.ru опрос',
            f'{interview.get_html()}',
            settings.EMAIL_HOST_USER,
            ['egorov_michil@mail.ru'] + settings.SEND_TO_EMAILS,
            fail_silently=True,
        )

        send_mail(
            'lotoslab.ru ответ на опрос',
            interview.generate_answer(),
            settings.EMAIL_HOST_USER,
            [interview.email],
            fail_silently=True,
            html_message=interview.generate_answer(),
        )


    return redirect(request.META.get('HTTP_REFERER', '/'))


def import_partners(request):
    for filename in os.listdir(settings.BASE_DIR + f'/export_data/partners'):
        if filename[-4:] != 'xlsx':
            continue

        df = pandas.read_excel(settings.BASE_DIR + f'/export_data/partners/' + filename)

        doctor_name = df.name[0]
        partner = Partner.get_partner_by_name(doctor_name)
        partner.name_en = partner.translit(doctor_name)

        if not partner.id is None:
            partner.specialization = df.type[0]
            partner.specialization_en = partner.translit(df.type[0])

        partner.description = df['info'][0]
        partner.save()

        package_name = df.package[0]
        package = PartnerPackage.get_package_by_nam_and_partner(package_name, partner)
        package.partner = partner
        package.save()
        package.analysis.clear()

        for code_invitro in df.code_invitro:
            analys = Analys.objects.filter(labaratory__name='Инвитро', code=code_invitro).first()

            if not analys is None:
                package.analysis.add(analys)

        for code_helix in df.code_helix:
            analys = Analys.objects.filter(labaratory__name='Лаборатория-партнёр', code=code_helix).first()

            if not analys is None:
                package.analysis.add(analys)

        package.save()

    return HttpResponse('Успешно')


def generate_cart_url(request):
    return render(request, 'main/generate_cart_url.html')


def handler404(request, *args, **argv):
    response = render(request, 'old/page11813515.html')
    response.status_code = 404
    return response
