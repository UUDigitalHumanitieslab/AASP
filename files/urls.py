from django.conf.urls import url
from django.urls import path

from files.views import ProvideFilesView, overview_files, download_files, \
    fda_smoothing, fda_select_tier, fda_select_interval

urlpatterns = [
    path('', ProvideFilesView.as_view()),
    path('analyze', overview_files),
    path('download', download_files),
    path('fda_smoothing', fda_smoothing),
    path('fda_select_tier', fda_select_tier),
    path('fda_select_interval/<int:tier>', fda_select_interval)
]