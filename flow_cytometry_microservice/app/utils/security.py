import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from app.models import flow_cytometry, gating

load_dotenv()
FLOW_CYTOMETRY_SECRET_KEY = os.getenv('FLOW_CYTOMETRY_SECRET_KEY')

def encrypt_data(data):
    """
    Encrypts data using Fernet symmetric encryption
    
    Args:
        data (str): Data to encrypt
    
    Returns:
        bytes: Encrypted data
    """
    try:
        fernet = Fernet(FLOW_CYTOMETRY_SECRET_KEY)
        return fernet.encrypt(data.encode('utf-8'))
    except Exception as e:
        print(f"Error encrypting data: {str(e)}")
        raise Exception("Failed to encrypt data")

def decrypt_data(data):
    """
    Decrypts data using Fernet symmetric encryption
    
    Args:
        data (bytes): Data to decrypt
    
    Returns:
        str: Decrypted data
    """
    try:
        fernet = Fernet(FLOW_CYTOMETRY_SECRET_KEY)
        return fernet.decrypt(data).decode('utf-8')
    except Exception as e:
        print(f"Error decrypting data: {str(e)}")
        raise Exception("Failed to decrypt data")
    
# permission check function (username, project and membership)
def check_permission(username, project_id):
    # check that the user exists
    user = flow_cytometry.UserModel.find_by_username(username)
    if user is None:
        return {"error": "User not found"}, 404
    # check that the project exists
    project = flow_cytometry.ProjectModel.find_by_progressive_id(project_id)
    if project is None:
        return {"error": "Project not found"}, 404
    # check if the user is a member of the project
    membership = flow_cytometry.MemberModel.find_by_user_id_project_id(int(user['progressive_id']), int(project_id))
    if membership is None:
        return {"error": "User not a member of the project"}, 403
    return {"message": "User has permission to access the project"}, 200
    
    
    
    