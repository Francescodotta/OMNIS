import pyopenms as oms

def link_features(feature_files, output_consensus_file):
    # Load feature maps
    feature_maps = []
    for file in feature_files:
        fmap = oms.FeatureMap()
        oms.FeatureXMLFile().load(file, fmap)
        fmap.ensureUniqueId()  # Ensure unique ID for the feature map
        for feature in fmap:
            feature.ensureUniqueId()  # Ensure unique ID for each feature
        #fmap.setPrimaryMSRunPath([file])  # Set the MS run path for traceability
        feature_maps.append(fmap)
    # Prepare consensus map
    consensus_map = oms.ConsensusMap()
    # Feature linking
    linker = oms.FeatureGroupingAlgorithmKD()
    linker.group(feature_maps, consensus_map)
    # Store consensus map
    oms.ConsensusXMLFile().store(output_consensus_file, consensus_map)
    print(f"Consensus map saved to {output_consensus_file}")

if __name__ == "__main__":
    feature_files = [
        "aligned_0.featureXML",
        "aligned_1.featureXML",
        # add more files as needed
    ]
    link_features(feature_files, "final.consensusXML")