import copy

from urllib.parse import urlparse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse_lazy, resolve
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail
from django.conf import settings

from shop.cart import Cart
from analysis.models import (AnalysInBranch, LabaratoryBranch, City, Analys,
                            LabaratoryBranchShop, Matched)

from shop.models import Order, PromoCode


def ordering(request):
    cart = Cart(request)
    error = 0
    lab_shop = None

    if request.method == "POST":
        if "save" in request.POST:
            order = Order.make_order(request)

            if order is None:
                error = 1
            else:
                url = order.tinkoff_request()

                if not url is None:
                    cart.clear()
                    return redirect(url)

            return render(request, 'shop/ordering.html', locals())

        elif "make_order" in request.POST:
            lab_shop_id = request.POST.get('lab_shop_id')
            lab_shop = LabaratoryBranchShop.objects.get(id=lab_shop_id)
            labaratory = lab_shop.labaratory

            ids = []
            for id, _ in request.session['cart'].items():
                if AnalysInBranch.objects.filter(id=id, labaratory_branch=labaratory).first() == None:
                    ids.append(id)

            for id in ids:
                product = AnalysInBranch.objects.get(id=id)
                cart.remove(product)

            lab_shop_name = request.POST.get('lab_shop_name', None)

            return render(request, 'shop/ordering.html', locals())

    return redirect('/')


@csrf_exempt
def payment(request):
    def body_to_dict():
        body = request.body.decode('utf-8')
        replaces = {"true": "True", 'false': "False", 'none': "None"}
        for x in replaces:
            body = body.replace(x, replaces[x])

        return eval(body)

    try:
        send_mail(
            'логи',
            str(request.body),
            settings.EMAIL_HOST_USER,
            ['egorov_michil@mail.ru']
        )
    except:
        pass

    post = body_to_dict()

    if request.method == "POST":
        if post['TerminalKey'] != settings.TINKOFF_TERMINAL_KEY:
            return JsonResponse({'error': '1'})

        payment_id = post['PaymentId']
        order = Order.objects.get(payment_id=payment_id)
        status = post['Status']

        if status == 'CONFIRMED':
            order.is_verified = True
            order.save()

            send_mail(
                'lotoslab.ru покупка',
                f'{order.get_html()}',
                settings.EMAIL_HOST_USER,
                ['egorov_michil@mail.ru', order.email] + settings.SEND_TO_EMAILS
            )

            send_mail(
                'Направление пациента lotoslab.ru',
                order.to_lab_html(),
                settings.EMAIL_HOST_USER,
                [order.labaratory_shop.gen_lab.email]
            )

        return HttpResponse('OK')

    return JsonResponse({'error': '0'})


@csrf_exempt
def press_to_buy(request):
    if request.method == "POST":
        name = request.POST.get('name')
        birthday = request.POST.get('birthday')
        email = request.POST.get('email')
        analysis = request.POST.get('analysis').split(',')

        nl = '\n'
        answer = f"""
ФИО: {name}
Дата рождения: {birthday}
Email: {email}
Анализы:
{nl.join(analysis)}
        """

        send_mail(
            'Заказ готовится к оплате',
            answer,
            settings.EMAIL_HOST_USER,
            settings.SEND_TO_EMAILS
        )

    return JsonResponse({"error": 0})


def cart_add(request, id):
    cart = Cart(request)
    product = AnalysInBranch.objects.get(id=id)

    city = City.get_city_by_name(request.session.get('city_name', 'sankt-peterburg'))

    matched = product.matched
    if not matched is None:
        for analys in matched.analysis_by_city(city):
            cart.add(analys, matched_id=matched.id)
    else:
        cart.add(product)

    return redirect(reverse_lazy("shop:cart_detail"))


def item_clear(request, id):
    cart = Cart(request)
    product = AnalysInBranch.objects.get(id=id)
    city = City.get_city_by_name(request.session.get('city_name', 'sankt-peterburg'))

    matched = product.matched
    if not matched is None:
        for analys in matched.analysis_by_city(city):
            cart.remove(analys)
    else:
        cart.remove(product)

    return redirect(reverse_lazy("shop:cart_detail"))


def item_increment(request, id):
    cart = Cart(request)
    product = AnalysInBranch.objects.get(id=id)
    city = City.get_city_by_name(request.session.get('city_name', 'sankt-peterburg'))

    matched = product.matched
    if not matched is None:
        for analys in matched.analysis_by_city(city):
            cart.add(analys, matched_id=matched.id)
    else:
        cart.add(product)

    return HttpResponse(cart.products_count)


def item_decrement(request, id):
    cart = Cart(request)
    product = AnalysInBranch.objects.get(id=id)
    cart.decrement(product=product)
    return redirect(reverse_lazy("shop:cart_detail"))


def cart_clear(request):
    cart = Cart(request)
    cart.clear()
    return redirect(reverse_lazy("shop:cart_detail"))


def cart_detail(request):
    city_name = request.session.get('city_name', 'sankt-peterburg')
    city = City.get_city_by_name(city_name)
    cart = Cart(request)
    labaratory_list = LabaratoryBranch.objects.filter(city=city, labaratory__is_active=True, is_tapable=True)

    return render(request, 'shop/cart_detail.html', locals())


def cart_change_city(request, new_city_name):
    def get_changed_url():
        resolved_url = resolve(urlparse(request.META.get('HTTP_REFERER', '/')).path)
        url_name = resolved_url.namespaces[0] + ':' + resolved_url.url_name
        kwargs = resolved_url.kwargs
        if 'city_name' in kwargs:
            kwargs['city_name'] = new_city_name

        return reverse_lazy(url_name, kwargs=kwargs)

    cart = Cart(request)

    request.session['city_name'] = new_city_name

    new_city = City.get_city_by_name(new_city_name)
    new_cart = copy.deepcopy(cart.cart)
    cart.clear()

    for _, product in new_cart.items():
        analys = Analys.objects.get(id=product['analys_id'])
        new_product = AnalysInBranch.objects.filter(analys=analys,
                                   labaratory_branch__city=new_city).first()

        if not new_product is None:
            cart.add(new_product, matched_id=product['matched_id'])

    return redirect(get_changed_url())


def fill_cart_by_url(request):
    products_id = eval(request.GET.get('products', '[]').replace('%20', ''))

    cart = Cart(request)
    cart.clear()

    for product_id in products_id:
        analys = Analys.objects.get(id=product_id)
        city = City.get_city_by_name(request.session.get('city_name', 'sankt-peterburg'))

        product = AnalysInBranch.objects.filter(
            labaratory_branch__city=city,
            analys=analys).first()

        if not product is None:
            cart_add(request, product.id)

    return redirect(reverse_lazy("shop:cart_detail"))


def get_promocode_by_text(request):
    text = request.GET.get('promocode_text', '')
    promocode = PromoCode.get_promocode(text)

    discount = 0

    if not promocode is None:
        discount = promocode.discount

    return JsonResponse({'discount': discount})
