import pyopenms as oms
import os
import glob

def idmap_features(aligned_feature_files, mzml_files_list, output_dir):
    mapper = oms.IDMapper()

    for feature_file in aligned_feature_files:
        fmap = oms.FeatureMap()
        oms.FeatureXMLFile().load(feature_file, fmap)

        # Get the spectra_data meta value (should match mzML filename)
        if fmap.getMetaValue("spectra_data"):
            spectra_data = fmap.getMetaValue("spectra_data")[0].decode()
        else:
            # Fallback: try to match by order or filename
            spectra_data = os.path.basename(feature_file).replace("aligned_", "").replace(".featureXML", ".mzML")

        # Find the corresponding mzML file
        mzml_file = None
        for mf in mzml_files_list:
            if os.path.basename(mf) == os.path.basename(spectra_data):
                mzml_file = mf
                break
        if mzml_file is None:
            print(f"No matching mzML file found for {feature_file}, skipping.")
            continue

        exp = oms.MSExperiment()
        oms.MzMLFile().load(mzml_file, exp)

        peptide_ids = []
        protein_ids = []
        mapper.annotate(fmap, peptide_ids, protein_ids, True, True, exp)

        output_file = os.path.join(output_dir, "IDMapped_" + os.path.basename(feature_file))
        oms.FeatureXMLFile().store(output_file, fmap)
        print(f"Annotated and saved: {output_file}")

if __name__ == "__main__":
    aligned_feature_files = [
        "aligned_0.featureXML",
        "aligned_1.featureXML",
        # add more if needed
    ]
    mzml_files_list= ["/media/datastorage/it_cast/omnis_microservice_db/test_db/20250228_04_03.mzML", "/media/datastorage/it_cast/omnis_microservice_db/test_db/20250228_04_02.mzML"]
    output_dir = "./"  # or your preferred output directory
    idmap_features(aligned_feature_files, mzml_files_list, output_dir)