
from collections import Counter
from zipfile import ZipFile
import os
import os.path as op
import io
import glob

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.core.files.uploadhandler import MemoryFileUploadHandler, TemporaryFileUploadHandler
from django.views.decorators.csrf import csrf_exempt, csrf_protect


from files.forms import SpeakerDirectoryForm
from files.models import AASPItem

files_error_message = "AASP couldn't extract pairs of .TextGrid and .wav files \
    from the directory you tried to upload. \
    Make sure that you have pairs of .TextGrid and .wav files with the same name \
    (e.g., 'de_muis_at_kaas.TextGrid' & 'de_muis_at_kaas.wav') in your directory \
    and then retry the upload."

class ProvideFilesView(FormView):
    form_class = SpeakerDirectoryForm
    template_name = 'drop_files.html'
    success_url = '../analyze'

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist('files')
        created_items = 0
        if form.is_valid():
            file_names = list(set([op.splitext(op.basename(str(f)))[0] for f in files]))
            for fn in file_names:
                wav_file = next((f for f in files if op.basename(
                    str(f)) == '{}.wav'.format(fn)), None)
                tg_file = next((f for f in files if op.basename(
                    str(f)) == '{}.TextGrid'.format(fn)), None)
                if not wav_file or not tg_file:
                    continue
                new_item = AASPItem(
                    item_id=fn, speaker=request.POST['label'], wav_file=wav_file, text_grid_file=tg_file)
                new_item.save()
                created_items += 1
            if not created_items:
                return HttpResponse(files_error_message)
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class DownloadView(TemplateView):
    template_name = 'files/download.html'

    def post(self, request, method, *args, **kwargs):
        s = io.BytesIO()
        zf = ZipFile(s, "w")
        output_selector = '{}_output/*.*'.format(method)
        for analyzed_file in glob.glob(output_selector):
            zf.write(analyzed_file)
            os.remove(analyzed_file)
        zf.close()
        response = HttpResponse(
            s.getvalue(), content_type="application/x-zip-compressed")
        response['Content-Disposition'] = 'attachment; filename=results.zip'
        return response
