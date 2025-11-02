# ...existing code...
import os
import subprocess

# local paths - adjust as needed
base_db_dir = "/media/datastorage/it_cast/omnis_microservice_db/tools"
mapping_file = os.path.join(base_db_dir, "plant_metabolites.tsv")   # your mapping file
struct_file  = os.path.join(base_db_dir, "plant_metabolites.sdf")   # your structure file

# recommended OpenMS default adducts (download if not present)
positive_adducts = os.path.join(base_db_dir, "PositiveAdducts.tsv")
negative_adducts = os.path.join(base_db_dir, "NegativeAdducts.tsv")

cmd = [
    "AccurateMassSearch",
    "-in", "/media/datastorage/it_cast/metabolomica/test/decharged.featureXML",
    "-out", "/media/datastorage/it_cast/metabolomica/test/accurate_mass.mzTab",
    "-db:mapping", mapping_file,
    "-db:struct", struct_file,
    "-positive_adducts", positive_adducts,
    "-negative_adducts", negative_adducts,
    # "-out_annotation", "/media/datastorage/it_cast/metabolomica/test/decharged.annotated.featureXML",  # optional
]

# example run (uncomment to execute)
# subprocess.run(cmd, check=True)
# ...existing code...