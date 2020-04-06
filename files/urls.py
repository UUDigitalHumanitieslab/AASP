from django.conf.urls import url
from django.urls import path

from files.views import ProvideFilesView, overview_files, download_files

urlpatterns = [
    path('', ProvideFilesView.as_view()),
    path('analyze', overview_files),
    path('download', download_files)
]