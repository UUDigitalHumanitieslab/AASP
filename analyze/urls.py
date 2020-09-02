from django.conf.urls import url
from django.urls import path

from analyze.views import AnalyzeView, \
    fda_smoothing, FDASelectTierView, FDASelectIntervalView

from analyze.charts import get_gcv_err_plot, get_combined_images

urlpatterns = [
    path('', AnalyzeView.as_view(), name='analyze'),
    path('fda_smoothing', fda_smoothing),
    path('fda_select_tier', FDASelectTierView.as_view(), name='fda_select_tier'),
    path('tier/<int:tier>/fda_select_interval/', FDASelectIntervalView.as_view(), name='fda_select_interval'),
    path('charts/gcverr', get_gcv_err_plot),
    path('charts/combined', get_combined_images)
]