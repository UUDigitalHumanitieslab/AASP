import os.path as op
import os
from collections import Counter
import subprocess
from zipfile import ZipFile
import io
import glob
import csv

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic.edit import FormView
from django.core.files.uploadhandler import MemoryFileUploadHandler, TemporaryFileUploadHandler
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.template import loader

import parselmouth # Praat wrapper
import pympi # pympi-ling for textgrid processing
import pandas as pd

from files.forms import SpeakerDirectoryForm
from files.models import AASPItem

csv_file_name = op.join('input_files', 'data.csv')

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
    success_url = 'analyze'

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


def overview_files(request):
    template = loader.get_template('files/overview_files.html')
    item_list = AASPItem.objects.all()
    context = {
        'item_list': item_list,
    }
    if request.method == "POST":
        analysis_set = request.POST.getlist('checked_files')
        if not op.exists('output'):
            os.makedirs('output')
        if 'autodi' in request.POST:
            for item_id in analysis_set:
                item = item_list.get(pk=item_id)
                analyze_ToDI(item)
            return redirect(download_files)
        elif 'fda' in request.POST:
            with open(csv_file_name, 'w+') as f:        
                csv_writer = csv.DictWriter(f, 
                fieldnames=('filename', 'spk'))
                csv_writer.writeheader()
                for item_id in analysis_set:
                    item = item_list.get(pk=item_id)
                    analyze_pitches_FDA(item)
                    line = {
                        'filename': item.item_id,
                        'spk': item.speaker,
                    }
                    csv_writer.writerow(line)
            return redirect(fda_select_tier)
    else:
        return HttpResponse(template.render(context, request))


def fda_select_tier(request):
    if request.method == "POST":
        tier = request.POST.get('tier')[0]
        return redirect(fda_select_interval, tier)
    df = pd.read_csv(csv_file_name)
    # check the first file in the analysis batch (directly under header)
    check_file = get_tg_name(df.iloc[0]['filename'])
    tg = pympi.Praat.TextGrid(check_file)
    tiers = tg.get_tier_name_num()
    tier_names = ['{}: {}'.format(t[0], t[1]) for t in tiers]
    return render(request, 'files/fda_select_tier.html', {'tier_list': tier_names})


def fda_select_interval(request, tier):
    df = pd.read_csv(csv_file_name)
    if request.method == "POST":
        interval = request.POST.get('interval')[0]
        start_times = []
        end_times = []
        for index, f in df.iterrows():
            tg = pympi.Praat.TextGrid(get_tg_name(f['filename']))
            iv = list(tg.get_tier(tier).get_intervals())[int(interval)-1]
            start_times.append(int(iv[0]*1000))
            end_times.append(int(iv[1]*1000))
        dois = pd.DataFrame({'doi_start_time': start_times, 'doi_end_time': end_times})
        df_with_dois = df.join(dois)
        df_with_dois.to_csv(op.join('input_files', 'data_with_dois.csv'), index=False)
        return HttpResponse('ok')
    check_file = get_tg_name(df.iloc[0]['filename'])
    tg = pympi.Praat.TextGrid(check_file)
    tier = tg.get_tier(tier)
    ivs = tier.get_intervals()
    interval_list = ['{}: {}'.format(index+1, i[2]) for index, i in enumerate(ivs)]
    return render(request, 'files/fda_select_interval.html', {'interval_list': interval_list})


def fda_smoothing(request):
    return render(request, 'files/fda_smoothing.html', {})

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


def analyze_ToDI(item):
    tg = item.text_grid_file
    wav = item.wav_file
    identifier = item.item_id
    call = ["java", "-jar", "AuToDI/AuToBI.jar",
        "-input_file={}".format(tg),
        "-wav_file={}".format(wav),
        "-out_file=output/{}_output.TextGrid".format(op.splitext(op.basename(str(wav)))[0]),
        "-pitch_accent_detector=AuToDI/v3.7.5_pitch_accent_detection.model",
        "-pitch_accent_classifier=AuToDI/v3.7.5_pitch_accent_classification.model",
        "-intonational_phrase_boundary_detector=AuToDI/bdc_burnc.intonp.dection.model",
        "-intermediate_phrase_boundary_detector=AuToDIbdc_burnc.interp.detection.model",
        "-boundary_tone_classifier=AuToDI/v3.7.5_boundary_tone_classification.model",
        "-phrase_accent_classifier=AuToDI/bdc_burnc.phacc.classification.model",
        "-words_tier_name=segment",
        "-tones_tier_name=intonation"
    ]
    subprocess.check_call(call)

def analyze_pitches_FDA(item):
    wav = str(item.wav_file)
    if not item.pitch_file:
        sound = parselmouth.Sound(wav)
        # get pitches at 5 ms intervals
        pitches = sound.to_pitch(0.005)
        selected_pitches = pitches.selected_array
        # get formants with Burg method
        formants = sound.to_formant_burg(0.005)
        filename = '{}.pitch'.format(op.splitext(op.basename(wav))[0])
        with open(op.join('input_files', filename), 'w+') as f:
            outfile = csv.DictWriter(f, fieldnames=('time', 'f0', 'f1bark', 'f2bark', 'roi'))
            outfile.writeheader()
            for index, t in enumerate(formants.ts()):
                # get formant 1 and 2 for each time unit
                f1 = formants.get_value_at_time(1, t, parselmouth.FormantUnit.BARK)
                f2 = formants.get_value_at_time(2, t, parselmouth.FormantUnit.BARK)
                outfile.writerow({
                    'time': int(round(t*1000)), 
                    'f0': selected_pitches[index][0],
                    'f1bark': f1,
                    'f2bark': f2,
                })
        item.pitch_file = filename
        item.save()


def get_tg_name(filename):
    return op.join('input_files', filename + '.TextGrid')