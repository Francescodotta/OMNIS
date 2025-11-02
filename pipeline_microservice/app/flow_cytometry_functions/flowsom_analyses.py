import flowsom as fs
import pytometry as pm
import scanpy as sc
import csv 
import numpy as np
import matplotlib.pyplot as plt


# set default logging parameters
plt.rcParams["figure.figsize"] = (6.5, 4.8)
plt.rcParams["figure.dpi"] = 300
plt.rcParams["font.size"] = 10




ff = fs.io.read_FCS("/media/datastorage/it_cast/omnis_microservice_db/flow_cytometry/project_13/Spleenocytes_Tcells_Rag2KO_005.fcs")
print(ff)