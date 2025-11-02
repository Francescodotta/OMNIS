from app.utils.security import hash_password, verify_password, create_jwt, validate_email, decrypt_email
from app.models.auth_models import UserModel    
import cryptography.fernet as fernet
import os
from dotenv import load_dotenv

load_dotenv()

FERNET_SECRET_KEY = os.getenv('FERNET_SECRET_KEY')


## funzione per validare i dati dall'input di registrazione 
def validate_registration_data(data):
    if not data.get('username') or not data.get('password') or not data.get('email'):
        return {"message": "Missing required fields, please check your input"}, 400
    if UserModel.find_by_email(data.get('email')):
        return {"message": "Email already exists, please choose another one"}, 400
    if UserModel.find_by_username(data.get('username')):
        return {"message": "Username already exists, please choose another one"}, 400
    if not validate_email(data.get('email')):
        return {"message": "Invalid email format, please check your input"}, 400
    db_fields = UserModel.db_fields
    # all the fields in the data must be present in the db_fields
    for field in data:
        if field not in db_fields:
            return {"message": f"Invalid field: {field}"}, 400
    # all the data types must match the ones defined in db_fields
    for field, value in data.items():
        expected_type = db_fields[field]
        if not isinstance(value, expected_type):
            return {"message": f"Invalid type for field {field}: expected {expected_type}, found {type(value)}"}, 400
    # password must be at least 8 characters long with a number
    if len(data.get('password')) < 8 or not any(char.isdigit() for char in data.get('password')):
        return {"message": "Password must be at least 8 characters long with a number"}, 400
    # all the db fields must be present in the form
    for field in db_fields:
        if field not in data:
            return {"message": f"Missing required field: {field}"}, 400
    return None, 200


def validate_change_password_data(data, username):
    if not data.get('old_password') or not data.get('new_password'):
        return {"message": "Missing required fields, please check your input"}, 400

    # check that the old password matches with the one in the db
    user = UserModel.find_by_username(username)
    if not user:
        return {"message": "User not found"}, 404
    if not verify_password(data.get('old_password'), user.get('password')):
        return {"message": "Invalid credentials"}, 401
    
    if data.get('old_password') == data.get('new_password'):
        return {"message": "Old and new password cannot be the same"}, 400

    # lunga abbastanza e contiene almeno un numero
    if len(data.get('new_password')) < 8 or not any(char.isdigit() for char in data.get('new_password')):
        return {"message": "Password must be at least 8 characters long with a number"}, 400

    return None, 200


def validate_update_user_data(data):
    db_fields = UserModel.db_fields

    # Controlla che tutti i campi nei dati siano presenti in db_fields
    for field in data:
        if field not in db_fields:
            raise ValueError(f"Campo non valido: {field}")

    # Controlla che i tipi di dati corrispondano a quelli definiti in db_fields
    for field, value in data.items():
        expected_type = db_fields[field]
        if not isinstance(value, expected_type):
            raise TypeError(f"Tipo non valido per il campo {field}: atteso {expected_type}, trovato {type(value)}")
    
    # controlla che lo username sia univoco. Se lo username è lo stesso di quello dell'utente che sta facendo la richiesta, allora è ok, fai questo check tramite il progressive id dell'utente
    if data.get('username'):
        user = UserModel.find_by_username(data.get('username'))
        if user and user.get('progressive_id') != data.get('progressive_id'):
            return {"message": "Username already exists, please choose another one"}, 400
        
    # controlla che l'email sia univoca. Se l'email è la stessa di quella dell'utente che sta facendo la richiesta, allora è ok, fai questo check tramite il progressive id dell'utente
    if data.get('email'):
        user = UserModel.find_by_email(data.get('email'))
        if user and user.get('progressive_id') != data.get('progressive_id'):
            return {"message": "Email already exists, please choose another one"}, 400

    return None, 200

def is_user_admin(username):
    user = UserModel.find_by_username(username)
    if not user:
        return {"message": "User not found"}, 404
    # decrypt the role
    f = fernet.Fernet(FERNET_SECRET_KEY)
    user['role'] = f.decrypt(user.get('role')).decode('utf-8')
    if user.get('role') != 'admin':
        return False
    return True



def validate_login_user(data):
    if not data.get('username') or not data.get('password'):
        return {"message": "Missing required fields, please check your input"}, 400
    print(data)
    user = UserModel.find_by_username(data.get('username'))
    print(user)
    # decrypt   

    if not user:
        return {"message": "User not found"}, 404
    
    if not verify_password(data.get('password'), user.get('password')):
        return {"message": "Invalid credentials"}, 401
    
    return user, 200