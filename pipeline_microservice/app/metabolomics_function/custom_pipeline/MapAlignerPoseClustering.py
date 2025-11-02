import subprocess
import os

cmd = [
    "MapAlignerPoseClustering",
    "-in", 
    "/media/datastorage/it_cast/metabolomica/test/CC1.mzML", 
    "/media/datastorage/it_cast/metabolomica/test/CC2.mzML",
    "-out", 
    "/media/datastorage/it_cast/metabolomica/test/aligned1.mzML", 
    "/media/datastorage/it_cast/metabolomica/test/aligned2.mzML",
    "-reference:file", "/media/datastorage/it_cast/metabolomica/test/CC1.mzML",
]

subprocess.run(cmd, capture_output=True, text=True, check=True)