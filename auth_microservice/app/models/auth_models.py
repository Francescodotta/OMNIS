from app import mongo
from app.utils.security import decrypt_email


class UserModel():

    db_fields = {
        "username": str,
        "nome": str,
        "cognome": str,
        "affiliazione": str,
        "role": str,
        "posizione": str,
        "laboratorio": str,
        "tier": str,
        "password": str,    
        "email": str,
    }

    @staticmethod
    def get_next_sequence():
        sequence = mongo.db.user_counter.find_one_and_update(
            {"_id": "project_id"},
            {"$inc": {"sequence_value": 1}},
            return_document=True,
            upsert=True  # Aggiungi upsert=True per creare il documento se non esiste
        )

        # Se sequence è None, inizializza il contatore
        if sequence is None:
            mongo.db.user_counter.insert_one({"_id": "project_id", "sequence_value": 1})
            return 1

        return sequence["sequence_value"]

    @staticmethod
    def create_user(user_data):
        user_data["progressive_id"] = UserModel.get_next_sequence()
        return mongo.db.users.insert_one(user_data)
    
    @staticmethod
    def find_by_username(username):
        return mongo.db.users.find_one({"username": username})
    

    @staticmethod
    def find_by_email(email):
        ## decrypt all the emails in the database for the check
        for user in mongo.db.users.find():
            if decrypt_email(user.get('email')) == email:
                return user
        return None


    @staticmethod
    def update_user(user_id, updated_data):
        return mongo.db.users.update_one({"_id": user_id}, {"$set": updated_data})
    
    @staticmethod
    def find_user_by_id(user_id):
        return mongo.db.users.find_one({"progressive_id": user_id})


    @staticmethod
    def get_all_users():
        # escludi le password nella risposta
        return mongo.db.users.find({}, {"password": 0})
    
    @staticmethod
    def delete_user_by_username(username):
        return mongo.db.users.delete_one({"username": username})