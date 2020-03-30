from django.contrib import admin

import subprocess
from os.path import abspath, basename, splitext

from .models import AASPItem


def analyze_FDA(modeladmin, request, queryset):
    for item in queryset:
        tg = item.text_grid_file
        call = ["Rscript", "FDA/FDA.R", abspath(str(tg))]
        subprocess.check_call(call)


def analyze_ToDI(modeladmin, request, queryset):
    for item in queryset:
        tg = item.text_grid_file
        wav = item.wav_file
        identifier = item.item_id
        call = ["java", "-jar", "AuToDI/AuToBI.jar",
            "-input_file={}".format(tg),
            "-wav_file={}".format(wav),
            "-out_file=output/{}_output.TextGrid".format(splitext(basename(str(wav)))[0]),
            "-pitch_accent_detector=AuToDI/bdc_burnc.acc.detection.model",
            "-pitch_accent_classifier=AuToDI/v3.7.5_pitch accent classification.model",
            "-intonational_phrase_boundary_detector=AuToDI/bdc_burnc.intonp.dection.model",
            "-intermediate_phrase_boundary_detector=AuToDIbdc_burnc.interp.detection.model",
            "-boundary_tone_classifier=AuToDI/bdc_burnc.pabt.classification.model",
            "-phrase_accent_classifier=AuToDI/bdc_burnc.phacc.classification.model",
            "-words_tier_name=segment",
            "-tones_tier_name=intonation"
        ]
        subprocess.check_call(call)


analyze_ToDI.short_description = "Get ToDI tones for selected files"
analyze_FDA.short_description = "Get Functional Data Analyses for selected files"


@admin.register(AASPItem)
class AASPItemAdmin(admin.ModelAdmin):
    model = AASPItem
    actions = [analyze_FDA, analyze_ToDI]