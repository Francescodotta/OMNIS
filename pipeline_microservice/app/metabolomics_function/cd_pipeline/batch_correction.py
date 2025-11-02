import pyopenms as oms
import numpy as np
import os

def normalize_feature_maps_tic(feature_files, reference_index=0, output_dir=None):
    feature_maps = []
    for file in feature_files:
        fmap = oms.FeatureMap()
        oms.FeatureXMLFile().load(file, fmap)
        feature_maps.append(fmap)
    tics = [sum([f.getIntensity() for f in fmap]) for fmap in feature_maps]
    ref_tic = tics[reference_index]
    output_files = []
    for i, fmap in enumerate(feature_maps):
        ratio = ref_tic / tics[i] if tics[i] > 0 else 1.0
        for feature in fmap:
            feature.setIntensity(feature.getIntensity() * ratio)
        out_file = os.path.join(output_dir, os.path.basename(feature_files[i])) if output_dir else feature_files[i]
        oms.FeatureXMLFile().store(out_file, fmap)
        output_files.append(out_file)
    return output_files

def normalize_feature_maps_pqn(feature_files, reference_index=0, output_dir=None):
    feature_maps = []
    all_intensities = []
    for file in feature_files:
        fmap = oms.FeatureMap()
        oms.FeatureXMLFile().load(file, fmap)
        feature_maps.append(fmap)
        all_intensities.append(np.array([f.getIntensity() for f in fmap]))
    all_intensities = np.array(all_intensities)
    ref_profile = np.median(all_intensities, axis=0)
    quotients = all_intensities / ref_profile
    quotients[np.isnan(quotients)] = 1.0
    scaling_factors = np.median(quotients, axis=1)
    output_files = []
    for i, fmap in enumerate(feature_maps):
        for j, feature in enumerate(fmap):
            feature.setIntensity(feature.getIntensity() / scaling_factors[i])
        out_file = os.path.join(output_dir, os.path.basename(feature_files[i])) if output_dir else feature_files[i]
        oms.FeatureXMLFile().store(out_file, fmap)
        output_files.append(out_file)
    return output_files

def normalize_feature_maps(feature_files, reference_index=0, method="tic", output_dir=None):
    if method == "pqn":
        return normalize_feature_maps_pqn(feature_files, reference_index, output_dir)
    else:
        return normalize_feature_maps_tic(feature_files, reference_index, output_dir)