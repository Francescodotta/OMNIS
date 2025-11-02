import cryptography.fernet  

# crea la chiave di crittografia fernet
def create_fernet_key():
    key = cryptography.fernet.Fernet.generate_key()
    return key


#salva la chiave un file
def save_key_to_file(key, filename):
    with open(filename, 'wb') as file:
        file.write(key)


save_key_to_file(create_fernet_key(), 'fernet.key')