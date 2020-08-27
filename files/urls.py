from django.conf.urls import url
from django.urls import path

from files.views import ProvideFilesView, download_files

urlpatterns = [
    path('', ProvideFilesView.as_view()),
]