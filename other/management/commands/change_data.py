from django.core.management.base import BaseCommand

from analysis.views import (refresh_analysis, import_matcheds, import_samplings,
                    refresh_analys_sections, import_shops)

from other.views import import_partners
from transliterate import translit


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('func_name', type=str, help='Function')

    def handle(self, **kwargs):
        try:
            func_name = kwargs['func_name']
            print(f'Starting command {func_name}...')
            r = eval(func_name)(1)
            print(translit(r.content.decode('utf-8'), 'ru', reversed=True))
        except:
            print('Wrong function name')
