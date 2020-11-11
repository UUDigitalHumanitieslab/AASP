import csv
import os.path as op
import subprocess

import parselmouth # Praat wrapper

def analyze_ToDI(item):
    tg = item.text_grid_file
    wav = item.wav_file
    identifier = item.item_id
    call = ["java", "-jar", "AuToDI/AuToBI.jar",
        "-input_file={}".format(tg),
        "-wav_file={}".format(wav),
        "-out_file=AuToDI_output/{}_output.TextGrid".format(op.splitext(op.basename(str(wav)))[0]),
        "-pitch_accent_detector=AuToDI/v3.7.5_pitch_accent_detection.model",
        "-pitch_accent_classifier=AuToDI/v3.7.5_pitch_accent_classification20200504.model",
        "-intonational_phrase_boundary_detector=AuToDI/v3.7.5_prosodic_boundary_detection20200504.model",
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
            outfile = csv.DictWriter(f, fieldnames=('time', 'f0', 'f1bark', 'f2bark'))
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