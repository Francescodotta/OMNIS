# crea la secret key utilizzata per criptare i dati con cryptography
import os
from cryptography.fernet import Fernet

# crea la secret key
FLOW_CYTOMETRY_SECRET_KEY = Fernet.generate_key()
# salva la secret key in un file
with open("flow_cytometry_secret_key.key", "wb") as file:
    file.write(FLOW_CYTOMETRY_SECRET_KEY)
