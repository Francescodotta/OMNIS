import pyopenms as oms
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

METABOLOMICS_SAVE_PATH = os.getenv("METABOLOMICS_BASE_PATH")

# create the function for the alignment of the files
def align_featureXML_files(feature_files):
    """
    Aligns featureXML files using the MapAlignmentAlgorithmPoseClustering algorithm.
    
    Parameters:
    feature_files (list): List of featureXML file names to be aligned.
    
    Returns:
    dict: Alignment metrics including RT statistics before and after alignment.
    """
    # empty list to store feature maps
    feature_maps = []
    # for each feature file, load the feature map and append it to the list
    for feature_file in feature_files:
        feature_map = oms.FeatureMap()
        oms.FeatureXMLFile().load(feature_file, feature_map)
        feature_maps.append(feature_map)
        print(f"Number of features in {feature_file}: {feature_map.size()}")
    # set ref_index to feature map index with the largest number of features
    ref_index = [
        i[0]
        for i in sorted(
            enumerate([fm.size() for fm in feature_maps]), key=lambda x: x[1]
        )
    ][0]
    print(f"Reference map index: {ref_index}")
    
    # Collect RTs before alignment for metrics
    rts_before = []
    for fmap in feature_maps:
        rts_before.append([f.getRT() for f in fmap])

    # push all maps except the reference into the align method
    feature_maps_to_align = feature_maps[:ref_index] + feature_maps[ref_index + 1 :]
    # define the aligner
    aligner = oms.MapAlignmentAlgorithmPoseClustering()
    aligner.setReference(feature_maps[ref_index])
    # parameters
    aligner_params = aligner.getDefaults()
    aligner.setParameters(aligner_params)
    # perform alignment and transformation of feature maps to the reference map
    # perform alignment and transformation of feature maps to the reference map
    for i, feature_map in enumerate(feature_maps):
        if i == ref_index:
            # Reference map: save as aligned as-is
            output_file = os.path.join(METABOLOMICS_SAVE_PATH, f"aligned_{i}.featureXML")
            print(f"Saving reference feature map to {output_file}")
            oms.FeatureXMLFile().store(output_file, feature_map)
        else:
            trafo = oms.TransformationDescription()
            aligner.align(feature_map, trafo)
            transformer = oms.MapAlignmentTransformer()
            transformer.transformRetentionTimes(feature_map, trafo, True)
            # store original RT as meta value in feature map
            for feature in feature_map:
                feature.setMetaValue("original_RT", feature.getRT())
                
            output_file = os.path.join(METABOLOMICS_SAVE_PATH, f"aligned_{i}.featureXML")
            # debug the saved file
            print(f"Saving aligned feature map to {output_file}")
            oms.FeatureXMLFile().store(output_file, feature_map)

    # Collect RTs after alignment for metrics
    rts_after = []
    for fmap in feature_maps:
        rts_after.append([f.getRT() for f in fmap])

    # Calculate RT statistics for metrics
    metrics = {
        "num_files": len(feature_files),
        "features_per_file": [len(rts) for rts in rts_before],
        "rt_mean_before": [np.mean(rts) if rts else None for rts in rts_before],
        "rt_std_before": [np.std(rts) if rts else None for rts in rts_before],
        "rt_mean_after": [np.mean(rts) if rts else None for rts in rts_after],
        "rt_std_after": [np.std(rts) if rts else None for rts in rts_after],
    }

    print("\nAlignment metrics:")
    for i, fname in enumerate(feature_files):
        print(f"File: {fname}")
        print(f"  Features: {metrics['features_per_file'][i]}")
        print(f"  RT mean before: {metrics['rt_mean_before'][i]:.2f}, after: {metrics['rt_mean_after'][i]:.2f}")
        print(f"  RT std before: {metrics['rt_std_before'][i]:.2f}, after: {metrics['rt_std_after'][i]:.2f}")

    return metrics
    
    
if __name__ == "__main__":
    # test the function
    feature_files = [
        "/media/datastorage/it_cast/omnis_microservice_db/test_db/20231006_NA_01_feature_map.featureXML",
        "/media/datastorage/it_cast/omnis_microservice_db/test_db/20231006_NA_02_feature_map.featureXML",
    ]
    align_featureXML_files(feature_files)