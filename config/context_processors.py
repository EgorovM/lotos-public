from analysis.models import City
from shop.cart import Cart

def lotos_processors(request):
    kwargs = {
        'cities': City.objects.all(),
        'current_city': request.session.get('city_name', 'sankt-peterburg'),
        'cart_item_count': Cart(request).products_count
    }

    kwargs['current_city_obj'] = City.get_city_by_name(kwargs['current_city'])

    return kwargs
