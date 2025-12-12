import os
from pymongo import MongoClient
from app.utils.security import hash_password, encrypt_data  # Importa da security

# Configurazione MongoDB
MONGO_URI = os.getenv('MONGO_URI_AUTH', 'mongodb://localhost:27017/auth_db')
client = MongoClient(MONGO_URI)
db = client.get_database()

# Controlla se ci sono già utenti
if db.users.count_documents({}) > 0:
    print("Utenti già presenti nel DB. Salto la creazione dell'admin.")
    client.close()
    exit(0)

# Dati dell'utente admin (cripta tutto tranne username e password)
admin_data = {
    "username": "admin",
    "nome": encrypt_data("admin"),
    "cognome": encrypt_data("admin"),
    "affiliazione": encrypt_data("Platform"),
    "role": encrypt_data("admin"),
    "posizione": encrypt_data("Administrator"),
    "laboratorio": encrypt_data("OMNIS"),
    "tier": encrypt_data("premium"),
    "password": hash_password("admin"),  # Usa hash_password da security
    "email": encrypt_data("admin@omnis.com"),
}

# Logica per progressive_id
def get_next_sequence():
    sequence = db.user_counter.find_one_and_update(
        {"_id": "project_id"},
        {"$inc": {"sequence_value": 1}},
        return_document=True,
        upsert=True
    )
    if sequence is None:
        db.user_counter.insert_one({"_id": "project_id", "sequence_value": 1})
        return 1
    return sequence["sequence_value"]

# Crea l'utente
admin_data["progressive_id"] = get_next_sequence()
result = db.users.insert_one(admin_data)

print(f"Utente admin creato con ID: {result.inserted_id}")
client.close()