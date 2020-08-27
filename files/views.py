
from collections import Counter
from zipfile import ZipFile
import os.path as op
import io
import glob

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic.edit import FormView
from django.core.files.uploadhandler import MemoryFileUploadHandler, TemporaryFileUploadHandler
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from files.forms import SpeakerDirectoryForm
from files.models import AASPItem


# class CustomMemoryFileUploadHandler(MemoryFileUploadHandler):
#     def new_file(self, *args, **kwargs):
#         args = (args[0], args[1].replace('/', '-').replace('\\', '-')) + args[2:]
#         super(CustomMemoryFileUploadHandler, self).new_file(*args, **kwargs)


# class CustomTemporaryFileUploadHandler(TemporaryFileUploadHandler):
#     def new_file(self, *args, **kwargs):
#         args = (args[0], args[1].replace('/', '-').replace('\\', '-')) + args[2:]
#         super(CustomTemporaryFileUploadHandler, self).new_file(*args, **kwargs)
        

class ProvideFilesView(FormView):
    form_class = SpeakerDirectoryForm
    template_name = 'drop_files.html'
    success_url = '../analyze'

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist('directory')
        if form.is_valid():
            file_names = Counter([op.splitext(op.basename(str(f)))[0] for f in files])
            pairs = [f for f in file_names.keys() if file_names[f]==2]
            for p in pairs:
                wav_file = next((f for f in files if op.basename(str(f))=='{}.wav'.format(p)), None)
                tg_file = next((f for f in files if op.basename(str(f))=='{}.TextGrid'.format(p)), None)
                new_item = AASPItem(item_id=p, speaker=request.POST['speaker'], wav_file=wav_file, text_grid_file=tg_file)
                new_item.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


def download_files(request):
    if request.method == "POST":
        s = io.BytesIO()
        zf = ZipFile(s, "w")
        for analyzed_file in glob.glob('output/*.TextGrid'):
            zf.write(analyzed_file)
        zf.close()
        response = HttpResponse(s.getvalue(), content_type="application/x-zip-compressed")
        response['Content-Disposition'] = 'attachment; filename=results.zip'
        return response
    else:
        return render(request, 'files/download.html', {})