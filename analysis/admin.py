from django.contrib import admin

from .models import (City, GeneralLabaratory, LabaratoryBranchShop, Analys,
                     AnalysInBranch, Matched, LabaratoryBranch,
                     SamplingType, SamplingInLabaratoryBranch)


admin.site.register(City)
admin.site.register(LabaratoryBranch)
admin.site.register(GeneralLabaratory)
admin.site.register(LabaratoryBranchShop)
admin.site.register(Analys)
admin.site.register(AnalysInBranch)
admin.site.register(Matched)
admin.site.register(SamplingType)
admin.site.register(SamplingInLabaratoryBranch)
