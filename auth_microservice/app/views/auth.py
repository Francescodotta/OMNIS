from app.models.auth_models import UserModel
from app.utils.security import hash_password, create_jwt, create_refresh_jwt_token
from app.helpers.auth import validate_registration_data, validate_login_user
import app.helpers.auth as auth_helpers
import logging
import os
from cryptography.fernet import Fernet
import logging

# Configura logging per eventuali errori
logger = logging.getLogger("custom_info_logger")

# configura la crittografia
FERNET_SECRET_KEY = os.getenv('FERNET_SECRET_KEY')    


## funzione per registrare un nuovo utente
def register_user(data, username):
    user = UserModel.find_by_username(username)
    if not user or not user.get("role"):
        logger.error(f"User {username} does not have a role")
        return {"error": "You are not authorized to register a new user."}, 403
    if not auth_helpers.is_user_admin(username):
        logger.error(f"User {username} is not authorized to register a new user")
        return {"error": "You are not authorized to register a new user."}, 403
    validation_error, status_code = validate_registration_data(data)
    if status_code != 200:
        logger.error(f"Error registering user: {validation_error['message']}")
        return validation_error, status_code
    logger.info(f"Registering user: {data['username']}")
    password_hash = hash_password(data['password'])
    ## cripta tutti i dati apparte la password utilizzando fernet
    fernet = Fernet(FERNET_SECRET_KEY)
    # ogni campo di data deve essere criptato secondo l'algoritmo di fernet tranne l'email e la password
    data['password'] = password_hash
    for key in data:
        if key != 'password' and key != 'username':
            data[key] = fernet.encrypt(data[key].encode('utf-8'))   
    ## inserisci l'utente nel db
    try:
        # data["username"] = username
        usermodel = UserModel.create_user(data)
        # check that the user model is created
        print(usermodel)
        if not usermodel:
            logger.error(f"Error registering user: {str(e)}")
            return {"error": "Failed to register user. Please try again later."}, 500
        logger.info(f"User {data['username']} registered successfully")
        return {"msg": "User registered successfully"}, 201
    ## altrmimenti gestisci l'errore
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        return {"error": "Failed to register user. Please try again later."}, 500
    


# funzione per modificare la password di un utente
def change_password_views(data, username):
    validation_error, status_code = auth_helpers.validate_change_password_data(data, username)
    logger.info(f"Changing password for user: {username}")
    if status_code != 200:
        logger.error(f"Error changing password: {validation_error['message']}")
        return validation_error, status_code
    user = UserModel.find_by_username(username)
    new_password_hash = hash_password(data['new_password'])
    try:
        UserModel.update_user(user['progressive_id'], {"password": new_password_hash})
        logger.info(f"Password changed successfully for user {username}")
        return {"msg": "Password changed successfully"}, 200
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        return {"error": "Failed to change password. Please try again later."}, 500



# update user
def update_user_views(data, username):
    validation_error, status_code = auth_helpers.validate_update_user_data(data)
    logger.info(f"Updating user: {data['username']}")
    if status_code != 200:
        logger.error(f"Error updating user: {validation_error['message']}")
        return validation_error, status_code
    
    # only the admin can update the role
    user = UserModel.find_by_username(username)
    if user['role'] != 'admin':
        data.pop('role')
    
    # se sta modificando la password hasha la nuova password
    if data.get('password'):
        data['password'] = hash_password(data['password'])
        ## cripta tutti i dati apparte la password utilizzando fernet
        fernet = Fernet(FERNET_SECRET_KEY)
        # ogni campo di data deve essere criptato secondo l'algoritmo di fernet tranne l'email e la password
        for key in data:
            if key != 'password' and key != 'username':
                data[key] = fernet.encrypt(data[key].encode('utf-8'))
        try:
            UserModel.update_user(data['progressive_id'], data)
            logger.info(f"User {data['username']} updated successfully")
            return {"msg": "User updated successfully"}, 200
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            return {"error": "Failed to update user. Please try again later."}, 500
        


# funzione per effettuare il login dell'utente
def login_user(data):
    print(data)
    fernet = Fernet(FERNET_SECRET_KEY)
    validated_user, status_code = validate_login_user(data)
    if status_code != 200:
        # add log
        return validated_user, status_code
    # get the role of the user
    user = UserModel.find_by_username(data['username'])
    if not user or not user.get("role"):
        logger.error(f"User {data['username']} does not have a role")
        return {"error": "You are not authorized to login."}, 403
    # get and decrypt the user data
    user_data = UserModel.find_by_username(data['username'])
    # decrypt the role of the userr
    user_data['role'] = fernet.decrypt(user_data['role']).decode('utf-8')
    access_token = create_jwt(validated_user['username'])
    refresh_token = create_refresh_jwt_token(validated_user['username'])
    return {"access_token": access_token, "refresh_token": refresh_token, "role": user_data["role"]}, 200



def get_user_views(username):
    user = UserModel.find_by_username(username)
    # check that the user is the admin
    if not auth_helpers.is_user_admin(username):
        return {"error": "You are not authorized to view this user."}, 403
    # find all the users in the db
    users = UserModel.get_all_users()
    #decrypt all the users data
    fernet = Fernet(FERNET_SECRET_KEY)
    users_list = []
    for user in users:
        print(user)
        user.pop('_id')
        for key in user:
            if key != 'progressive_id' and key != 'username':
                user[key] = fernet.decrypt(user[key]).decode('utf-8')
        users_list.append(user)
    logger.info(f"User {username} fetched all users successfully")
    return users_list, 200
    
def delete_user_views(username, admin_username):
    user = UserModel.find_by_username(admin_username)
    if not user or not user.get("role"):
        logger.error(f"User {admin_username} does not have a role")
        return {"error": "You are not authorized to delete a user."}, 403
    if not auth_helpers.is_user_admin(admin_username):
        logger.error(f"User {admin_username} is not authorized to delete a user")
        return {"error": "You are not authorized to delete a user."}, 403
    try:
        UserModel.delete_user_by_username(username)
        logger.info(f"User {username} deleted successfully")
        return {"msg": "User deleted successfully"}, 200
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        return {"error": "Failed to delete user. Please try again later."}, 500

