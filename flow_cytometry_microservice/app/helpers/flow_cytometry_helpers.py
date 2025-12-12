from app.utils.security import encrypt_data, decrypt_data
import os
import base64
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def encrypt_flow_cytometry_data(flow_data):
    """
    Encrypts sensitive flow cytometry data before storing it in the database
    
    Args:
        flow_data (dict): Dictionary containing flow cytometry data
    
    Returns:
        dict: Dictionary with encrypted sensitive data
    """
    try:
        # Fields to encrypt
        sensitive_fields = ['filename', 'description', 'file_path', 'workspace', 'timepoint']
        
        # Create a new dictionary with encrypted data
        encrypted_data = flow_data.copy()
        
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                # Convert to string if not already
                value = str(encrypted_data[field])
                # Encrypt the value using the security utility
                encrypted_value = encrypt_data(value)
                # assicurati che venga salvata una stringa decodificabile (Fernet -> base64 urlsafe)
                if isinstance(encrypted_value, bytes):
                    encrypted_data[field] = encrypted_value.decode('utf-8')
                else:
                    encrypted_data[field] = str(encrypted_value)

        return encrypted_data
    
    except Exception as e:
        logger.exception("Error encrypting flow cytometry data")
        raise Exception("Failed to encrypt flow cytometry data")

def decrypt_flow_cytometry_data(encrypted_data):
    try:
        sensitive_fields = ['filename', 'description', 'file_path', 'workspace', 'timepoint']
        decrypted_data = encrypted_data.copy()

        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                stored = decrypted_data[field]
                # non provare a decriptare se non sembra cifrato
                if not is_encrypted(stored):
                    continue
                try:
                    # supporta sia stringa che bytes
                    if isinstance(stored, str):
                        decrypted_value = decrypt_data(stored.encode('utf-8'))
                    elif isinstance(stored, (bytes, bytearray)):
                        decrypted_value = decrypt_data(bytes(stored))
                    else:
                        decrypted_value = stored
                    decrypted_data[field] = decrypted_value
                except Exception as e:
                    logger.debug("Unable to decrypt field '%s': %s", field, str(e))
                    # lascia il valore originale se la decrittazione fallisce
                    decrypted_data[field] = stored

        return decrypted_data

    except Exception as e:
        logger.exception("Error decrypting flow cytometry data")
        raise

# Utility function to check if data is already encrypted
def is_encrypted(data):
    """
    Checks if the given data is already encrypted
    
    Args:
        data (str): Data to check
    
    Returns:
        bool: True if data appears to be encrypted, False otherwise
    """
    try:
        if not isinstance(data, str):
            return False
        
        s = data.strip()
        # breve heuristica: deve essere base64-url-safe decodificabile e non troppo corto
        try:
            # aggiusta padding se necessario
            padding = '=' * (-len(s) % 4)
            decoded = base64.urlsafe_b64decode(s + padding)
            return len(decoded) > 8
        except Exception:
            return False
    except Exception:
        return False


def safe_decrypt(value):
    """
    Safely decrypt a value, returning the original value if decryption fails.
    """
    if isinstance(value, str) and value:
        # Check if it looks encrypted before attempting decryption
        if not is_encrypted(value):
            return value
        try:
            return decrypt_data(value.encode('utf-8'))
        except Exception as e:
            logger.debug("safe_decrypt: decryption failed for string: %s", str(e))
            return value
    elif isinstance(value, (bytes, bytearray)):
        try:
            return decrypt_data(bytes(value))
        except Exception as e:
            logger.debug("safe_decrypt: decryption failed for bytes: %s", str(e))
            return value
    # Return as-is for any other type or None
    return value
