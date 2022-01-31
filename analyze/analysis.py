import csv
import os.path as op
import subprocess
import pickle

import parselmouth # Praat wrapper
from scipy.io import arff
import pandas as pd
import numpy as np
import pympi  # pympi-ling for textgrid processing

from files.models import AASPItem

def get_features_ToDI(item, tier):
    """ call AuToBI to generate features,
    with all classifiers specified so they will be registered as tasks
    should collect a total of 740 features
    and store them in an .arff file
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

def classify_ToDI(analysis_set, tier_index):
    """ load the four classifiers for accent detection, accent classification, 
    boundary detection and boundary classification
    given an analysis_set (list of item ids), classify all segments
    write out a TextGrid file with results
    """
    with open('AuToDI/classifiers/pitch_accent_detection.pkl', 'rb') as f:
        accent_detector = pickle.load(f)
    with open('AuToDI/classifiers/pitch_accent_classification.pkl', 'rb') as f:
        accent_classifier = pickle.load(f)
    with open('AuToDI/classifiers/boundary_detection.pkl', 'rb') as f:
        boundary_detector = pickle.load(f)
    with open('AuToDI/classifiers/boundary_classification.pkl', 'rb') as f:
        boundary_classifier = pickle.load(f)
    features = accent_detector.feature_names_in_
    
    for identifier in analysis_set:
        item = AASPItem.objects.all().get(pk=identifier)
        arff_file = str(item.arff_file)
        with open(arff_file) as f:
            data, meta = arff.loadarff(f)
        df = pd.DataFrame(data)
        # select only the features used for training, replace NaN with 0
        X = df.loc[:, features].fillna(0)
        accented = accent_detector.predict(X)
        accent_classes = []
        for index, ac in enumerate(accented):
            if ac == 'accented':
                tone = [accent_classifier.predict(X.iloc[[index]])]
            else:
                tone = None
            accent_classes.append(tone)
        boundaries = boundary_detector.predict(X)
        boundary_classes = []
        for index, bo in enumerate(boundaries):
            if bo == True:
                boundary = [boundary_classifier.predict(X.iloc[[index]])]
            else:
                boundary = None
            boundary_classes.append(boundary)
        generate_text_grid(item, accent_classes, boundary_classes, tier_index)
    
def generate_text_grid(item, accent_classes, boundary_classes, tier_index):
    tg_file = item.text_grid_file
    tg = pympi.Praat.TextGrid(str(tg_file))
    tier = tg.get_tier(int(tier_index))
    # get all intervals from relevant tier, but skip intervals without text
    ivs = [i for i in tier.get_intervals() if i[2]!='']
    accent_tier = pympi.Praat.Tier(xmin=tier.xmin, xmax=tier.xmax, name='AuToDI-accent', tier_type='IntervalTier')
    boundary_tier = pympi.Praat.Tier(xmin=tier.xmin, xmax=tier.xmax, name='AuToDI-boundary', tier_type='IntervalTier')
    for index, iv in enumerate(ivs):
        start = iv[0]
        end = iv[1]
        if accent_classes[index]:
            value = accent_classes[index][0][0].replace('\\', '')
            accent_tier.add_interval(start, end, value)
        if boundary_classes[index]:
            value = boundary_classes[index][0][0].replace('\\', '')
            boundary_tier.add_interval(start, end, value)
    if list(accent_tier.get_intervals()):
        tg.add_tier('AuToDI-accent', 'IntervalTier')
        tg.tiers[-1] = accent_tier
    if list(boundary_tier.get_intervals()):
        tg.add_tier('AuToDI-boundary', 'IntervalTier')
        tg.tiers[-1] = boundary_tier
    output_name = op.join('AuToDI_output', '{}_output.TextGrid'.format(op.splitext(op.basename(str(tg_file)))[0]))
    tg.to_file(output_name)
        
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