import subprocess
import glob
import csv
import os.path as op
import os

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.views.generic.base import View, TemplateView
from django.urls import reverse

import parselmouth  # Praat wrapper
import pympi  # pympi-ling for textgrid processing
import pandas as pd

from files.views import DownloadView
from files.models import AASPItem

from analyze.analysis import analyze_pitches_FDA, analyze_ToDI

csv_file_name = op.join('input_files', 'data.csv')


class AnalyzeView(TemplateView):
    template_name = 'analyze/overview_files.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item_list = AASPItem.objects.all()
        speaker = self.request.GET.get('speaker')
        if speaker is not None and speaker != 'all':
            item_list = item_list.filter(speaker=speaker)
        speaker_list = AASPItem.objects.values_list('speaker', flat=True).order_by('speaker').distinct('speaker')
        context['sel_speaker'] = speaker
        context['item_list'] = item_list
        context['speaker_list'] = speaker_list
        return context

    def post(self, request, *args, **kwargs):
        analysis_set = request.POST.getlist('checked_files')
        if not op.exists('output'):
            os.makedirs('output')
        if 'delete' in request.POST:
            for id in analysis_set:
                AASPItem.objects.filter(pk=id).delete()
            url = reverse('analyze', args=self.args, kwargs=self.kwargs)
            return HttpResponseRedirect(url)
        elif 'autodi' in request.POST:
            for id in analysis_set:
                item = AASPItem.objects.all().get(pk=id)
                analyze_ToDI(item)
            return HttpResponseRedirect('../download/AuToDI')
        elif 'fda' in request.POST:
            with open(csv_file_name, 'w') as f:
                csv_writer = csv.DictWriter(f,
                                            fieldnames=('filename', 'spk'))
                csv_writer.writeheader()
                for id in analysis_set:
                    item = AASPItem.objects.all().get(pk=id)
                    analyze_pitches_FDA(item)
                    line = {
                        'filename': item.item_id,
                        'spk': item.speaker,
                    }
                    csv_writer.writerow(line)
            return HttpResponseRedirect('./fda_select_tier')


class FDASelectTierView(TemplateView):
    template_name = 'analyze/fda_select_tier.html'

    def get_context_data(self, **kwargs):
        df = pd.read_csv(csv_file_name)
        # check the first file in the analysis batch (directly under header)
        check_file = get_tg_name(df.iloc[0]['filename'])
        tg = pympi.Praat.TextGrid(check_file)
        tiers = tg.get_tier_name_num()
        tier_names = ['{}: {}'.format(t[0], t[1]) for t in tiers]
        return {'tier_list': tier_names}

    def post(self, request, *args, **kwargs):
        tier = request.POST.get('tier')[0]
        url = reverse('fda_select_interval', kwargs={'tier': tier})
        return HttpResponseRedirect(url)


class FDASelectIntervalView(View):
    def get_initialization_files(self):
        df = pd.read_csv(csv_file_name)
        check_file = get_tg_name(df.iloc[0]['filename'])
        tg = pympi.Praat.TextGrid(check_file)
        return df, tg

    def get(self, request, *args, **kwargs):
        df, tg = self.get_initialization_files()
        tier = tg.get_tier(kwargs['tier'])
        ivs = tier.get_intervals()
        interval_list = ['{}: {}'.format(index + 1, i[2]) for index, i in enumerate(ivs)]
        return render(request, 'analyze/fda_select_interval.html', {'interval_list': interval_list})

    def post(self, request, *args, **kwargs):
        df, tg = self.get_initialization_files()
        interval = int(request.POST.get('interval')[0])
        tier_no = int(kwargs['tier'])
        start_times = []
        end_times = []
        for index, f in df.iterrows():
            tg = pympi.Praat.TextGrid(get_tg_name(f['filename']))
            tier = tg.get_tier(tier_no)
            iv = list(tier.get_intervals())[interval - 1]
            start_times.append(int(iv[0] * 1000))
            end_times.append(int(iv[1] * 1000))
        df_with_rois = df.assign(roi_start_time=start_times, roi_end_time=end_times)
        df_with_rois.to_csv(op.join('input_files', 'data_with_rois.csv'), index=False)
        call = ["Rscript", "--vanilla", "FDA/PrepareFPCA.R"]
        output = subprocess.check_output(call).decode().split('\n')
        grid_lam = output[0].split(" ")[:-1]
        grid_knots = output[1].split(" ")[:-1]
        lam, knots = output[-1].split(" ")
        request.session.update({
            'lambda': lam, 'knots': knots,
            'grid_lam': grid_lam, 'grid_knots': grid_knots})
        return HttpResponseRedirect('../../../fda_smoothing')


class FDASmoothingView(View):
    def get(self, request, *args, **kwargs):
        arguments = ['lambda', 'knots', 'grid_lam', 'grid_knots']
        args = {key: request.session[key] for key in arguments}
        args['nharm_values'] = [1, 2, 3, 4, 5]
        args['nharm_preset'] = 3
        return render(request, 'analyze/fda_smoothing.html', args)

    def post(self, request, *args, **kwargs):
        lam = request.POST.get('lambda')
        knots = request.POST.get('knots')
        nharm = request.POST.get('nharm')
        call = ["Rscript", "--vanilla", "FDA/FPCA.R", lam, knots, nharm]
        output = subprocess.check_output(call)
        os.rename('/code/Rplots.pdf', '/code/FDA_output/PCA_f0reg.pdf')
        return HttpResponseRedirect('../download/FDA')


def get_tg_name(filename):
    return op.join('input_files', filename + '.TextGrid')
