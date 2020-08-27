import subprocess
import glob
import csv
import os.path as op
import os

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader

import parselmouth # Praat wrapper
import pympi # pympi-ling for textgrid processing
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

from files.views import download_files
from files.models import AASPItem

csv_file_name = op.join('input_files', 'data.csv')

def overview_files(request):
    template = loader.get_template('analyze/overview_files.html')
    item_list = AASPItem.objects.all()
    context = {
        'item_list': sorted(item_list, key=lambda x: x.item_id),
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
            with open(csv_file_name, 'w') as f:        
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
    return render(request, 'analyze/fda_select_tier.html', {'tier_list': tier_names})


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
        df_with_rois = df.assign(roi_start_time=start_times, roi_end_time=end_times)
        df_with_rois.to_csv(op.join('input_files', 'data_with_rois.csv'), index=False)
        call = ["Rscript", "--vanilla", "FDA/FDA.R"]
        output = subprocess.check_output(call).decode().split('\n')
        grid_lam = output[0].split(" ")[:-1]
        grid_knots = output[1].split(" ")[:-1]
        lam, knots = output[-1].split(" ")
        return render(request, 'analyze/fda_smoothing.html', {
            'lam':lam, 'knots':knots, 
            'grid_lam': grid_lam, 'grid_knots': grid_knots})
    check_file = get_tg_name(df.iloc[0]['filename'])
    tg = pympi.Praat.TextGrid(check_file)
    tier = tg.get_tier(tier)
    ivs = tier.get_intervals()
    interval_list = ['{}: {}'.format(index+1, i[2]) for index, i in enumerate(ivs)]
    return render(request, 'analyze/fda_select_interval.html', {'interval_list': interval_list})


def fda_smoothing(request, lam, knots, grid_lam, grid_knots):
    return render(request, 'analyze/fda_smoothing.html', {'lam': lam, 'knots': knots})


def get_gcv_err_plot(request):
    img = Image.open(op.join('/', 'code', 'plots', 
        'GCV_log_err_f0.png'))
    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")
    return response
    

def get_combined_images(request):
    ''' combines all plots generated by R into one image,
    returns it as an img/png response
    '''
    plot_list = list(glob.glob('/code/plots/*.png'))
    height, width, intensity = np.asarray(Image.open(plot_list[0]).convert('RGB')).shape
    grid_lam = sorted(list(set([int(pl.split('_')[1]) for pl in plot_list if op.split(pl)[-1].startswith('f0')])))
    grid_knots = sorted(list(set([int(pl.split('_')[3]) for pl in plot_list if op.split(pl)[-1].startswith('f0')])))
    nrows = len(grid_lam)
    ncols = len(grid_knots)
    image_list = []
    for lam in grid_lam:
        for knot in grid_knots:
            plot = next((pl for pl in plot_list if op.split(pl)[-1].startswith('f0')
                         and int(pl.split("_")[1])==lam and 
                         int(pl.split("_")[3])==knot), None)
            if plot:
                image = np.array(Image.open(plot).convert('RGB'))
            else:
                # paste white image
                image = np.zeros([height,width,3]).fill(255)
            image_list.append(image)
    result = np.array(image_list).reshape(
        nrows, ncols, height, width, intensity).swapaxes(
            1,2).reshape(
                height*nrows, width*ncols, intensity)
    img = Image.fromarray(result)
    for pl in plot_list:
        os.remove(pl)
    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")
    return response


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
