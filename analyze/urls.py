from django.conf.urls import url
from django.urls import path

from analyze.views import overview_files, \
    fda_smoothing, fda_select_tier, fda_select_interval

urlpatterns = [
    path('', overview_files),
    path('fda_smoothing', fda_smoothing),
    path('fda_select_tier', fda_select_tier),
    path('fda_select_interval/<int:tier>', fda_select_interval)
]