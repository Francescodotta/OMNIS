import subprocess
import os

cmd = [
    "MetaboliteSpectralMatcher",
    "-in", "/media/datastorage/it_cast/metabolomica/test/linked.featureXML",
    "-out", "/media/datastorage/it_cast/metabolomica/test/matched.mzTab",
    "-library", "/media/datastorage/it_cast/omnis_microservice_db/tools/GNPS-LIBRARY.mzML",
]

subprocess.run(cmd, check=True)
os.remove("/media/datastorage/it_cast/metabolomica/test/matched.mzTab")
os.remove("/media/datastorage/it_cast/metabolomica/test/linked.featureXML")
os.remove("/media/datastorage/it_cast/metabolomica/test/linked.consensusXML")
os.remove("/media/datastorage/it_cast/metabolomica/test/matched.featureXML")
os.remove("/media/datastorage/it_cast/metabolomica/test/matched.consensusXML")
os.remove("/media/datastorage/it_cast/metabolomica/test/matched.idXML")
