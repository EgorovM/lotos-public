from django.shortcuts import render, redirect
from django.urls import reverse_lazy

from analysis.models import City
from shop.views import cart_change_city


def parametrized(dec):
    def layer(*args, **kwargs):
        def repl(f):
            return dec(f, *args, **kwargs)
        return repl
    return layer


@parametrized
def check_session_city_name(function_to_decorate, url):
    def checking(request, **kwargs):
        city_name = kwargs['city_name']
        session_city_name = request.session.get('city_name', 'sankt-peterburg')

        city = City.get_city_by_name(city_name)

        if city is None:
            return redirect('/eror')

        if session_city_name != city_name:
            cart_change_city(request, city_name)
            return redirect(reverse_lazy(url, kwargs=kwargs))

        return function_to_decorate(request, **kwargs)

    return checking
