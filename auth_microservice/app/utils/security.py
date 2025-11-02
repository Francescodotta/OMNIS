from flask_jwt_extended import create_access_token, create_refresh_token
import bcrypt
import re, os
from cryptography.fernet import Fernet
from email_validator import validate_email, EmailNotValidError
FERNET_SECRET_KEY = os.getenv('FERNET_SECRET_KEY')    

# Funzione per hashare la password
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Funzione per verificare la password
def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

# Funzione per creare un JWT
def create_jwt(username):
    """
    This function creates a JWT (JSON Web Token) for a given user ID.
    
    Parameters:
        user_id (int): The ID of the user
    
    Returns:
        str: A JWT token
    """
    return create_access_token(identity=str(username))

# Funzione per creare un refresh JWT token
def create_refresh_jwt_token(username):
    """
    This function creates a refresh JWT token for a given user ID.
    
    Parameters:
        user_id (int): The ID of the user
    
    Returns:
        str: A refresh JWT token
    """

    return create_refresh_token(identity={"username": username})


def basic_email_check(email: str) -> bool:
    """
    Perform basic email format validation.
    
    Args:
        email: The email address to validate
        
    Returns:
        bool: True if email passes basic checks, False otherwise
    """
    # Remove leading/trailing whitespace
    email = email.strip()
    
    # Basic checks
    if not email:  # Check if empty
        return False
        
    if len(email) > 254:  # RFC 5321 length limit
        return False
    
    # Check for exactly one @
    if email.count('@') != 1:
        return False
    
    # Split into local and domain parts
    local, domain = email.split('@')
    
    # Check local and domain part lengths
    if len(local) > 64:  # RFC 5321 limit
        return False
    if len(domain) > 255:
        return False
    
    # Check if local or domain are empty
    if not local or not domain:
        return False
    
    return True

def validate_email(email: str) -> tuple[bool, str]:
    """
    Validate email using pattern matching.
    
    Args:
        email: Email address to validate
        
    Returns:
        tuple: (is_valid, reason)
    """
    if not basic_email_check(email):
        return False, "Failed basic format check"
    
    # Pattern for allowed characters in local part
    local_pattern = r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+$'
    
    # Pattern for domain (includes internationalized domains)
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$'
    
    local, domain = email.split('@')
    
    # Check local part
    if not re.match(local_pattern, local):
        return False, "Invalid characters in local part"
    
    # Check for consecutive special characters
    if '..' in local:
        return False, "Consecutive dots not allowed"
    
    if local[0] == '.' or local[-1] == '.':
        return False, "Local part cannot start or end with dot"
    
    # Check domain
    if not re.match(domain_pattern, domain):
        return False, "Invalid domain format"
    
    return True, "Valid email address"




# Funzione per criptare i dati
def encrypt_data(data):
    fernet = Fernet(FERNET_SECRET_KEY)
    return fernet.encrypt(data.encode('utf-8'))

def decrypt_email(encrypted_email):
    f = Fernet(FERNET_SECRET_KEY)
    decrypted_email = f.decrypt(encrypted_email).decode()
    print(decrypted_email)
    return decrypted_email