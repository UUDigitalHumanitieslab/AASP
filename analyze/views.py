import subprocess
import glob
import csv
import os.path as op
import os
import sys

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

import logging
logger = logging.getLogger('django')


csv_file_name = op.join('input_files', 'data.csv')
error_message = "Something went wrong. Contact digitalhumanities(at)uu(dot)nl for support."


class AnalyzeView(TemplateView):
    """ This view class provides an overview of all the uploaded files,
    and enables the user to start analysis with AuToDI, FDA,
    or to delete files.
    """
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
        if not analysis_set:
            return HttpResponse('You did not select any files.')
        if not op.exists('output'):
            os.makedirs('output')
        session_dict = {'analysis_set': analysis_set}
        request.session.update(session_dict)
        if 'delete' in request.POST:
            for identifier in analysis_set:
                AASPItem.objects.filter(pk=identifier).delete()
            url = reverse('analyze', args=self.args, kwargs=self.kwargs)
            return HttpResponseRedirect(url)
        elif 'autodi' in request.POST:
            if len(analysis_set) > 30:
                return HttpResponse('AASP currently does not support AuToDI analysis of more than 30 files.')
            return HttpResponseRedirect('./select_tier/AuToDI')
        elif 'fda' in request.POST:
            with open(csv_file_name, 'w') as f:
                csv_writer = csv.DictWriter(f,
                                            fieldnames=('filename', 'spk'))
                csv_writer.writeheader()
                for identifier in analysis_set:
                    item = AASPItem.objects.all().get(pk=identifier)
                    analyze_pitches_FDA(item)
                    line = {
                        'filename': item.item_id,
                        'spk': item.speaker,
                    }
                    csv_writer.writerow(line)
            return HttpResponseRedirect('./select_tier/FDA')


class SelectTierView(TemplateView):
    """ This view class makes it possible to select a tier from the 
    .TextGrid data of the selected files.
    """
    template_name = 'analyze/select_tier.html'

    def get_context_data(self, method, **kwargs):
        context = super().get_context_data(**kwargs)
        analysis_set = self.request.session.get('analysis_set')
        # check the first file in the analysis batch
        item = AASPItem.objects.all().get(pk=analysis_set[0])
        check_file = str(item.text_grid_file)
        tg = pympi.Praat.TextGrid(check_file)
        tiers = tg.get_tier_name_num()
        tier_names = ['{}: {}'.format(t[0], t[1]) for t in tiers]
        return {'tier_list': tier_names}

    def post(self, request, method, *args, **kwargs):
        if method == 'FDA':
            tier = request.POST.get('tier').split(':')[0]
            url = reverse('fda_select_interval', kwargs={'tier': tier})
            return HttpResponseRedirect(url)
        elif method == 'AuToDI':
            tier = request.POST.get('tier').split(':')[1].strip()
            analysis_set = request.session.get('analysis_set')
            for identifier in analysis_set:
                item = AASPItem.objects.all().get(pk=identifier)
                analyze_ToDI(item, tier)
            return HttpResponseRedirect('../../download/AuToDI')
        else:
            return HttpResponse('This analysis method is not defined.')



class FDASelectIntervalView(View):
    """ This view class makes it possible to select an interval from the 
    .TextGrid data of the selected files, after the tier was selected previously.
    """
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
        interval = request.POST.get('interval')
        tier_no = int(kwargs['tier'])
        start_times = []
        end_times = []
        for index, f in df.iterrows():
            tg = pympi.Praat.TextGrid(get_tg_name(f['filename']))
            tier = tg.get_tier(tier_no)
            intervals = list(tier.get_intervals())
            if 'number' in request.POST:
                interval_no = int(interval.split(':')[0])
                iv = intervals[interval_no-1]
            elif 'text' in request.POST:
                interval_text = interval.split(': ')[1]
                iv = next((i for i in intervals if i[2]==interval_text), None)
                if not iv:
                    df.drop(index, inplace=True)
                    continue
            start_times.append(int(iv[0]*1000))
            end_times.append(int(iv[1]*1000))
        logger.info('Selected tier: {}'.format(tier_no))
        interval_definition = 'text' if request.POST.get('text') else 'number'
        logger.info('Selected interval {} by {}'.format(interval, interval_definition))
        df_with_rois = df.assign(roi_start_time=start_times, roi_end_time=end_times)
        df_with_rois.to_csv(op.join('input_files', 'data_with_rois.csv'), index=False)
        call = ["Rscript", "--vanilla", "FDA/PrepareFPCA.R"]
        try:
            output = subprocess.check_output(call).decode().split('\n')
        except subprocess.CalledProcessError as err:
            logger.error(err)
            return HttpResponse(error_message)
        logger.info(output)
        grid_lam = [int(o) for o in output[-7].split(" ")[:-1]]
        grid_knots = [int(o) for o in output[-6].split(" ")[:-1]]
        lam = int(output[-3])
        knots = int(output[-2])
        filename = output[-1]
        session_dict = {
            'lambda': lam, 'knots': knots,
            'grid_lam': grid_lam, 'grid_knots': grid_knots,
            'filename': filename}
        if len(output) > 7:
            # warnings about skipped files were generated
            skipped_files = [o.split(' ')[-2] for o in output[:-7]]
            session_dict['skipped'] = ', '.join(skipped_files)
        request.session.update(session_dict)
        return HttpResponseRedirect('../../../fda_smoothing')


class FDASmoothingView(View):
    """ This view class lets the user choose the smoothing parameters
    and number of principal components to be used for Functional Data Analysis.
    After selection, performs that analysis.
    """
    def get(self, request, *args, **kwargs):
        arguments = ['lambda', 'knots', 'grid_lam', 'grid_knots', 'filename', 'skipped']
        args = {key: request.session.get(key) for key in arguments}
        args['nharm_values'] = [1, 2, 3, 4, 5]
        args['nharm_preset'] = 3
        return render(request, 'analyze/fda_smoothing.html', args)

    def post(self, request, *args, **kwargs):
        lam = request.POST.get('lambda')
        knots = request.POST.get('knots')
        nharm = request.POST.get('nharm')
        call = ["Rscript", "--vanilla", "FDA/FPCA.R", lam, knots, nharm]
        try:
            output = subprocess.check_output(call)
        except subprocess.CalledProcessError as err:
            logger.error(err)
            return HttpResponse(error_message)
        os.rename('/code/Rplots.pdf', '/code/FDA_output/PCA_f0reg.pdf')
        return HttpResponseRedirect('../download/FDA')


def get_tg_name(filename):
    return op.join('input_files', filename + '.TextGrid')
