from django.conf.urls import url
from django.conf.urls.static import static
from django.urls import path
from django.conf import settings

from files.views import ProvideFilesView

urlpatterns = [
    path('', ProvideFilesView.as_view()),
]