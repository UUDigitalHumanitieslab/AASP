import csv
import os.path as op
import subprocess
import pickle

import parselmouth # Praat wrapper
from scipy.io import arff
import pandas as pd

def get_features_ToDI(item, tier):
    """ call AuToBI to generate features,
    with all classifiers specified so they will be registered as tasks
    should collect a total of 740 features
    """
    tg = item.text_grid_file
    wav = item.wav_file
    arff = '{}.arff'.format(op.splitext(tg.path)[0])
    identifier = item.item_id
    call = ["java", "-jar", "AuToDI/AuToBI.jar",
        "-input_file={}".format(tg),
        "-wav_file={}".format(wav),
        "-out_file=output/dumpme.TextGrid",
        "-arff_file={}".format(arff),
        "-pitch_accent_detector=AuToDI/bdc_burnc.acc.detection.model",
        "-pitch_accent_classifier=AuToDI/bdc_burnc.acc.classification.model ",
        "-intonational_phrase_boundary_detector=AuToDI/bdc_burnc.intonp.detection.model",
        "-intermediate_phrase_boundary_detector=AuToDI/bdc_burnc.interp.detection.model",
        "-boundary_tone_classifier=AuToDI/bdc_burnc.pabt.classification.model",
        "-phrase_accent_classifier=AuToDI/bdc_burnc.phacc.classification.model",
        "-words_tier_name={}".format(tier),
    ]
    subprocess.check_call(call)
    return arff

def classify_ToDI(arff_file):
    with open(arff_file) as f:
        data, meta = arff.loadarff(f)
    df = pd.DataFrame(data)
    with open('AuToDI/pitch_accent_detection.pkl', 'rb') as f:
        accent_detector = pickle.load(f)
        accented = accent_detector.predict(df)
        
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