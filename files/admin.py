from django.contrib import admin

import subprocess

from .models import AASPItem

def analyze(modeladmin, request, queryset):
    for item in queryset:
        tg = item.text_grid_file
        wav = item.wav_file
        identifier = item.item_id
        call = ["java", "-jar", "AuToBI.jar", 
            "-input_file={}".format(tg),
            "-wav_file={}".format(wav),
            "-arff_file=output/{}.arff".format(identifier)
        ]
        subprocess.check_call(call)
analyze.short_description = "Get features for selected files"

class AASPItemAdmin(admin.ModelAdmin):
    actions = [analyze]

admin.site.register(AASPItem, AASPItemAdmin)