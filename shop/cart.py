from decimal import Decimal

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect

from analysis.models import SamplingInLabaratoryBranch, Matched


class Cart(object):
    def __init__(self, request):
        self.request = request
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}

        self.cart = cart

    def add(self, product, quantity=1, action=None, matched_id=-1):
        """
        Add a product to the cart or update its quantity.
        """
        if not product.is_buyable:
            return

        id = product.id

        if matched_id == -1 or product.analys.code.startswith('Coronavirus'):
            name = product.name
        else:
            name = Matched.objects.get(id=matched_id).default_analys_name

        if str(product.id) not in self.cart.keys():
            self.cart[product.id] = {
                'userid': self.request.user.id,
                'analys_id': product.analys.id,
                'product_id': id,
                'matched_id': matched_id,
                'matched_labaratories': ";".join(product.matched_labaratories_by_id(matched_id)),
                'name': name,
                'quantity': 1,
                'name_en': product.analys.name_en,
                'price': str(product.price),
                'image': product.image.url,
                'labaratory': product.labaratory_branch.name,
                'samplings': [{'id': pr['id'], 'price': pr['price']} for pr in product.get_samplings()]
            }
        else:
            newItem = True

            for key, value in self.cart.items():
                if key == str(product.id):
                    value['quantity'] = value['quantity'] + 1
                    newItem = False
                    self.save()
                    break

            if newItem == True:
                self.cart[product.id] = {
                    'userid': self.request,
                    'analys_id': product.analys.id,
                    'product_id': product.id,
                    'matched_id': matched_id,
                    'matched_labaratories': ";".join(product.matched_labaratories_by_id(matched_id)),
                    'name': name,
                    'quantity': 1,
                    'name_en': product.analys.name_en,
                    'price': str(product.price),
                    'image': product.image.url,
                    'labaratory': product.labaratory_branch.name,
                    'samplings': [{'id': pr['id'], 'price': pr['price']} for pr in product.get_samplings()]
                }

        self.save()

    def save(self):
        # update the session cart
        self.session[settings.CART_SESSION_ID] = self.cart
        # mark the session as "modified" to make sure it is saved
        self.session.modified = True

    def remove(self, product):
        """
        Remove a product from the cart.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def decrement(self, product):
        for key, value in self.cart.items():
            if key == str(product.id):

                value['quantity'] = value['quantity'] - 1
                if(value['quantity'] < 1):
                    return redirect('cart:cart_detail')
                self.save()
                break
            else:
                print("Something Wrong")

    def clear(self):
        # empty cart
        self.session[settings.CART_SESSION_ID] = {}
        self.cart = {}
        self.session.modified = True

    def get_samplings(self):
        samplings = []

        names = set()
        ids = set()

        for _, value in self.cart.items():
            for sampling in value['samplings']:
                if not sampling['id'] in ids:
                    sm = SamplingInLabaratoryBranch.objects.get(id=sampling['id'])

                    if not sm.sampling_type.site_name in names:
                        samplings.append(sm)

                    names.add(sm.sampling_type.site_name)
                ids.add(sampling['id'])

        return samplings

    def get_samplings_with_labs(self):
        samplings = []

        stlns = set()
        ids = set()

        for _, value in self.cart.items():
            for sampling in value['samplings']:
                if not sampling['id'] in ids:
                    sm = SamplingInLabaratoryBranch.objects.get(id=sampling['id'])
                    stln = sm.sampling_type.site_name, sm.labaratory.name
                    if not stln in stlns:
                        samplings.append(sm)

                    stlns.add(stln)
                ids.add(sampling['id'])

        return samplings

    def get_custom_price(self, analys=False, sampling=False):
        analys_price = 0
        sampling_price = 0

        for _, value in self.cart.items():
            if analys:
                value['quantity'] = 1 #remove for quantity
                analys_price += (float(value['price']) * value['quantity'])

        if sampling:
            for sampling in self.get_samplings():
                sampling_price += sampling.price

        return analys_price + sampling_price

    @property
    def products_count(self):
        matched_ids = set()
        count = 0

        for _, product in self.cart.items():
            if product['matched_id'] == -1 or not product['matched_id'] in matched_ids:
                count += 1

            matched_ids.add(product['matched_id'])

        return count

    @property
    def sampling_price(self):
        return self.get_custom_price(sampling=True)

    @property
    def analys_price(self):
        return self.get_custom_price(analys=True)

    @property
    def total_price(self):
        return self.get_custom_price(analys=True, sampling=True)
