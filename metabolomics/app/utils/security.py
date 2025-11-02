import bcrypt
import re, os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

METABOLOMICS_SECRET_KEY = os.environ.get('METABOLOMICS_SECRET_KEY')


def encrypt_data(data):
    fernet = Fernet(METABOLOMICS_SECRET_KEY)
    return fernet.encrypt(data.encode('utf-8'))
    
# decripta i dati
def decrypt_data(data):
    fernet = Fernet(METABOLOMICS_SECRET_KEY)
    return fernet.decrypt(data).decode('utf-8')