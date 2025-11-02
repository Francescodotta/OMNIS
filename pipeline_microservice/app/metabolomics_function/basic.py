import pyopenms as oms

# leggi il file mzML
def read_mzML_file(file_path):
    exp = oms.MSExperiment()
    oms.MzMLFile().load(file_path, exp)
    return exp
